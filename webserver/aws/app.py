import asyncio
import base64
from collections.abc import AsyncIterable
from datetime import datetime
import time
from blacksheep import Application, Request, Response, StreamedContent, get, WebSocket, WebSocketDisconnectError, json, post, ws
from blacksheep.server.compression import GzipMiddleware
from blacksheep.server.sse import ServerSentEvent
from blacksheep.server.rendering.jinja2 import JinjaRenderer
from blacksheep.settings.html import html_settings
from blacksheep.server.responses import view_async
import os
from utils.logger import Log
from constants import HTTP_PORT, HTTPS_PORT, QUIC_PORT, PUBLIC_IP, stream_status, Format

app = Application(show_error_details=True)
html_settings.use(JinjaRenderer(enable_async=True))

app.use_cors(
    allow_methods="*",
    allow_origins="*",
    allow_headers="*",
)

app.middlewares.append(GzipMiddleware(min_size=100))

current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)
static_path = os.path.join(current_dir, 'static')
app.serve_files(source_folder=static_path, discovery=True)

@get("/")
def home(request: Request):
    #print(request.scope.items())
    return f"Hello, World! {datetime.now().isoformat()}"

'''
    Receive Video From Raspberry PI
'''
from constants import INCOMING_FORMAT, OUTGOING_FORMAT, PROTOCOL_FORMAT
from constants import frame_queues, INFERENCE_ENABLED
from handler import handle_jpg_to_jpg, handle_jpg_to_h264, handle_h264_to_jpg, handle_h264_to_h264, tcp_handle_jpg_to_jpg, tcp_handle_jpg_to_h264, tcp_handle_h264_to_jpg, tcp_handle_h264_to_h264, ctx
from inference import get_onnx_status

@app.after_start
async def start():
    if PROTOCOL_FORMAT == 'TCP':
        handlers = {
            ('JPG', 'JPG'): tcp_handle_jpg_to_jpg.start,
            ('JPG', 'H264'): tcp_handle_jpg_to_h264.start,
            ('H264', 'JPG'): tcp_handle_h264_to_jpg.start,
            ('H264', 'H264'): tcp_handle_h264_to_h264.start,
        }
    elif PROTOCOL_FORMAT == 'UDP':
        handlers = {
            ('JPG', 'JPG'): handle_jpg_to_jpg.start,
            ('JPG', 'H264'): handle_jpg_to_h264.start,
            ('H264', 'JPG'): handle_h264_to_jpg.start,
            ('H264', 'H264'): handle_h264_to_h264.start,
        }
    else:
        raise ValueError("Invalid Protocol Format")

    assert get_onnx_status() or not INFERENCE_ENABLED, "Please install onnxruntime package if inference is enabled!"

    handler = handlers.get((INCOMING_FORMAT.value, OUTGOING_FORMAT.value))
    if handler:
        await handler()
    else:
        raise NotImplementedError("Unsupported format combination")

@app.on_stop
async def cleanup_server():
    await asyncio.sleep(0.2)
    await ctx.cleanup()

@post("/reset_stream")
async def start_stream(request: Request):
    if request.method != "POST":
        return json({"error": True, "message": "Invalid Method"}, status=405)
    
    body: dict   = await request.json()
    message:str = body.get('message')
    auth:str    = body.get('auth')

    if message == 'INIT_STREAM' and auth == 'BAYU':
        if not stream_status['value']:
            stream_status['value'] = True
            return json({"error": False, "message": "STREAM CAN START", "first_time": True})
        else:
            if INCOMING_FORMAT.value == Format.H264.value and OUTGOING_FORMAT.value == Format.H264.value:
                await handle_h264_to_h264.reset()
            elif INCOMING_FORMAT.value == Format.H264.value and OUTGOING_FORMAT.value == Format.JPG.value:
                await handle_h264_to_jpg.reset()
            elif INCOMING_FORMAT.value == Format.JPG.value and OUTGOING_FORMAT.value == Format.H264.value:
                await handle_jpg_to_h264.reset()
            elif INCOMING_FORMAT.value == Format.JPG.value and OUTGOING_FORMAT.value == Format.JPG.value:
                await handle_jpg_to_jpg.reset()

            return json({"error": False, "message": "STREAM CAN START", "first_time": False})

    return json({"error": False})


''' 
    ServerSentEvents: Video Stream Endpoints (h264 codec)
'''
@get("/h264_stream")
async def h264_stream(request: Request) -> AsyncIterable[ServerSentEvent]:
    frame_queue = asyncio.Queue()
    frame_queues.append(frame_queue)

    try:
        while True:
            if await request.is_disconnected():
                Log.info("The request is disconnected!")
                break
            try:
                timestamp, packed_data = await frame_queue.get()
                age = time.time() - timestamp
                encoded = base64.b64encode(packed_data).decode("ascii")

                if age > 0.2:
                    Log.warning(f"Skipped old frame ({age:.3f}s old)")
                    continue
                yield ServerSentEvent({"message": encoded})

                await asyncio.sleep(0.005)
            except asyncio.CancelledError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                Log.exception(f"Error in frame generator: {e}")
    finally:
        if frame_queue in frame_queues:
            frame_queues.remove(frame_queue)

'''
    ServerSentEvents: Video Stream Endpoints (JPG)
'''
@get("/jpg_stream")
async def jpg_stream(request: Request):
    # Create a queue for the new client and add it to the list of queues
    frame_queue = asyncio.Queue()
    frame_queues.append(frame_queue)

    async def frame_generator():
        try:
            while True:
                if await request.is_disconnected():
                    Log.info("The request is disconnected!")
                    break

                try:
                    timestamp, frame_bytes = await frame_queue.get()
                    age = time.time() - timestamp
                    if age > 0.2:
                        Log.warning(f"Skipped old frame ({age:.3f}s old)")
                        continue
                    
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n\r\n"
                    )
                    await asyncio.sleep(0.005)
                except asyncio.CancelledError:
                    break
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    Log.exception(f"Error in frame generator: {e}")
        finally:
            if frame_queue in frame_queues:
                frame_queues.remove(frame_queue)

    return Response(
        200,
        content=StreamedContent(
            content_type=b"multipart/x-mixed-replace; boundary=frame",
            data_provider=frame_generator 
        )
    )

'''
    Websockets: Video Stream Endpoints (H264)
'''
@ws("/ws_h264_stream")
async def ws_h264_stream(websocket: WebSocket):
    await websocket.accept()

    frame_queue = asyncio.Queue()
    frame_queues.append(frame_queue)

    try:
        while True:
            msg = await websocket.receive_text()
            if msg == 'READY':
                Log.info("READY TO RECEIVE")
                break
            await asyncio.sleep(0.02)
        while True:
            try:
                timestamp, packed_data = await frame_queue.get()
                age = time.time() - timestamp

                if age > 0.2:
                    Log.warning(f"Skipped old frame ({age:.3f}s old)")
                    continue

                await websocket.send_bytes(packed_data)
                await asyncio.sleep(0.005)
            except asyncio.CancelledError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                Log.exception(f"Error in frame generator: {e}")
    except WebSocketDisconnectError:
        return
    finally:
        if frame_queue in frame_queues:
            frame_queues.remove(frame_queue)

'''
    HTML Content
'''
@get("/sse")
async def sse_html(request: Request):
    scheme = request.scope.get('scheme')
    http_ver = request.scope.get('http_version')
    if http_ver == '1.1':
        port = HTTP_PORT
    elif http_ver == '2':
        port = HTTPS_PORT
    else:
        port = QUIC_PORT
    return await view_async("sse.jinja", {"scheme": scheme, "port": port, "ip": PUBLIC_IP})

@get("/h264")
async def h264_ws_html(request: Request):
    http_ver = request.scope.get('http_version')
    if http_ver == '1.1':
        port = HTTP_PORT
        scheme = 'ws'
    elif http_ver == '2':
        port = HTTPS_PORT
        scheme = 'wss'
    else:
        port = QUIC_PORT
        scheme = 'wss'
    return await view_async("h264.jinja", {"scheme": scheme, "port": port, "ip": PUBLIC_IP})


@get("/mjpeg")
async def mjpeg_html(request: Request):
    scheme = request.scope.get('scheme')
    http_ver = request.scope.get('http_version')
    if http_ver == '1.1':
        port = HTTP_PORT
    elif http_ver == '2':
        port = HTTPS_PORT
    else:
        port = QUIC_PORT
    return await view_async("mjpeg.jinja", {"scheme": scheme, "port": port, "ip": PUBLIC_IP})