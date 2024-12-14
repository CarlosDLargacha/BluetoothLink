import time 
import os 
import platform 
import asyncio 
import shutil 
from watchdog.observers import Observer 
from watchdog.events import FileSystemEventHandler 
import socket 
import aiohttp 
from aiohttp import web

# Configuracion
SYNC_FOLDER = r"C:\Users\Carlos Daniel\Desktop\Nueva carpeta (2)"
REMOTE_IP = "IP_del_otro_ordenador"
PORT = 12345

class SyncHandler(FileSystemEventHandler):
    def __init__(self, sync_folder, remote_ip, port):
        self.sync_folder = sync_folder
        self.remote_ip = remote_ip
        self.port = port

    def on_any_event(self, event):
        if event.is_directory:
            return
        loop = asyncio.get_event_loop()
        loop.create_task(self.sync_file(event.src_path))

    async def sync_file(self, file_path):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'http://{self.remote_ip}:{self.port}/sync', data={'file': open(file_path, 'rb')}) as resp:
                    print(await resp.text())
        except Exception as e:
            print(f"Error al sincronizar el archivo {file_path}: {e}")

def start_sync_service(sync_folder, remote_ip, port):
    event_handler = SyncHandler(sync_folder, remote_ip, port)
    observer = Observer()
    observer.schedule(event_handler, sync_folder, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

async def handle_sync(request):
    data = await request.post()
    file = data['file']
    with open(os.path.join(SYNC_FOLDER, os.path.basename(file.filename)), 'wb') as f:
        shutil.copyfileobj(file.file, f)
    return web.Response(text="Archivo sincronizado")

async def start_server():
    app = web.Application()
    app.router.add_post('/sync', handle_sync)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"Servidor de sincronizacion escuchando en el puerto {PORT}")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_server())
    start_sync_service(SYNC_FOLDER, REMOTE_IP, PORT)
    loop.run_forever()

