import asyncio
from enum import Enum
from multiprocessing import Process
from typing import List, Optional
from asyncio import DatagramTransport, Queue, Task, Server
from inference import ShmQueue
from utils.logger import Log
from utils.public_ip import get_public_ip

frame_queues: List[Queue] = []
"""List of asyncio frame queues, one for each connected client on video_stream endpoint"""

decode_queue: Queue  = Queue()
encode_queue: Queue  = Queue()
jpg_queue: Queue     = Queue()
ordered_queue: Queue = Queue()

stream_status    = {"value": False}
protocol_closed  = {"value": False}
frame_dispatch_reset = {"value": False}

class ServerContext:
    def __init__(self):
        self.transport: Optional[DatagramTransport] = None
        self.infer_process: Optional[Process] = None
        self.input_queue: Optional[ShmQueue] = None
        self.output_queue: Optional[ShmQueue] = None
        self.consumer_task: Optional[Task] = None
        self.encode_task: Optional[Task] = None
        self.decode_task: Optional[Task] = None
        self.ordering_task: Optional[Task] = None
        self.jpg_producer_task: Optional[Task] = None
        self.protocol: any = None
        self.server:Optional[Server] = None

    async def cleanup(self):
        """Cleans up resources safely and cancels running tasks."""
        Log.info("cleaning server context !")
        try:
            if self.transport:
                self.transport.close()
                self.transport = None
        except Exception as e:
            Log.exception(f"Error at cleanup transport: {e}")

        try:
            if self.infer_process:
                self.infer_process.kill()
                self.infer_process.join()
                self.infer_process = None
        except Exception as e:
            Log.exception(f"Error at cleanup infer_process: {e}")

        try:
            if self.consumer_task:
                if self.output_queue is not None:
                    self.output_queue.stop()

                self.consumer_task.cancel()
                try:
                    await self.consumer_task
                except asyncio.CancelledError:
                    pass
                self.consumer_task = None
        except Exception as e:
            Log.exception(f"Error at cleanup consumer_task: {e}")

        try:
            if self.encode_task:
                self.encode_task.cancel()
                try:
                    await self.encode_task
                except asyncio.CancelledError:
                    pass
                self.encode_task = None
        except Exception as e:
            Log.exception(f"Error at cleanup encode_task: {e}")

        try:
            if self.decode_task:
                self.decode_task.cancel()
                try:
                    await self.decode_task
                except asyncio.CancelledError:
                    pass
                self.decode_task = None
        except Exception as e:
            Log.exception(f"Error at cleanup decode_task: {e}")

        try:
            if self.jpg_producer_task:
                self.jpg_producer_task.cancel()
                try:
                    await self.jpg_producer_task
                except asyncio.CancelledError:
                    pass
                self.jpg_producer_task = None
        except Exception as e:
            Log.exception(f"Error at cleanup jpg_producer_task: {e}")

        try:
            if self.ordering_task:
                self.ordering_task.cancel()
                try:
                    await self.ordering_task
                except asyncio.CancelledError:
                    pass
                self.ordering_task = None
        except Exception as e:
            Log.exception(f"Error at cleanup ordering_task: {e}")

        try:
            if self.output_queue:
                self.output_queue.stop()
                self.output_queue.cleanup()
                self.output_queue = None
        except Exception as e:
            Log.exception(f"Error at cleanup output_queue: {e}")        

        try:
            if self.input_queue:
                self.input_queue.stop()
                self.input_queue.cleanup()
                self.input_queue = None
        except Exception as e:
            Log.exception(f"Error at cleanup input_queue: {e}")        

        try:
            if self.server:
                self.server.close()
                print("Server shut down cleanly.")
        except Exception as e:
            Log.exception(f"Error at cleanup input_queue: {e}")    

class base_codec():
    def __init__(self, name: str, device_type: str = None):
        self.name = name
        self.device_type = device_type

# Config
class EC2Port(Enum):
    UDP_PORT_JPG_TO_JPG   = int(8085)
    UDP_PORT_JPG_TO_H264  = int(8085)
    UDP_PORT_H264_TO_JPG  = int(8086)
    UDP_PORT_H264_TO_H264 = int(8086)
    TCP_PORT_JPG_TO_JPG   = int(8087)
    TCP_PORT_JPG_TO_H264  = int(8087)
    TCP_PORT_H264_TO_JPG  = int(8088)
    TCP_PORT_H264_TO_H264 = int(8088)
    # {Incoming-format} _TO_ {Outgoing-format}
    # For same incoming protocol == Same ip because code for raspi_socket is same


class Format(Enum):
    JPG = "JPG"
    H264 = "H264"

FFMPEG_DIR       = r"C:\ffmpeg\bin"
INCOMING_FORMAT  = Format.H264      # Valid: JPG or H264
OUTGOING_FORMAT  = Format.H264      # Valid: JPG or H264
PROTOCOL_FORMAT  = 'TCP'           # Valid: UDP or TCP
INFERENCE_ENABLED = bool(True)
SHOW_FPS = bool(True)

encoder = base_codec('libx264')
decoder = base_codec('h264')

QUIC_PORT  = 4433  # quic
HTTP_PORT  = 80    # http 1.1
HTTPS_PORT = 8080  # http 2
PUBLIC_IP  = '127.0.0.1'  # get_public_ip() or '127.0.0.1'

