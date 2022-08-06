import asyncio
import aiofiles
import aiofiles.os

"""
#vamos a crear un archivo
async def main():
    #creamos un archivo sin contenido
    handle = await aiofiles.open('test_create.txt', mode = 'x')
    #cerramos el archivo
    handle.close()
"""
"""
async def main():
    async with aiofiles.open('test_write.txt', mode='w') as handle:
        await handle.write('hello world')
"""
"""
async def main():
    async with aiofiles.open('test_write.txt', mode='r') as handle:
        data = await handle.read()
    print(f'Read {len(data)} bytes')
"""
"""
async def main():
    #creamos un directorio
    await aiofiles.os.makedirs('tmp', exist_ok=True)
"""
"""
async def main():
    #creamos un archivo que puede ser interrumpible osea no bloqueante    
    async with aiofiles.open('files_rename.txt', mode='w') as handle:        
        await handle.write('hello world')
    #renombramos el archivo de nuevo de una forma no bloqueante
    await aiofiles.os.rename('files_rename.txt', 'files_rename2.txt')
"""

"""
async def main():
    async with aiofiles.open('files_move3.txt', mode='x') as handle:
        await handle.close()
    #creamos un directorio
    await aiofiles.os.makedirs('tmp', exist_ok=True)
    #mvemos el archivo dentro del directorio
    await aiofiles.os.replace('files_move3.txt', 'tmp/files_move3.txt')
"""

async def main():
    async with aiofiles.open("files_delete.txt", mode='x') as handle:
        handle.close()
    await aiofiles.os.remove("files_delete.txt")
"""
async def main():
    async with aiofiles.open("files_copy.txt", mode='w') as handle:
        await handle.write("hello world")
    #creamos la fuente y el destino
    handle_src = await aiofiles.open('files_copy.txt', mode='r')
    handle_dst = await aiofiles.open('files_copy2.txt', mode='w')
    #obtenemos el tamaño del dato en bytes
    stat_src = await aiofiles.os.stat('files_copy.txt')
    n_bytes = stat_src.st_size
    #obtenemos el descriptor
    fd_src = handle_src.fileno()
    fd_dst = handle_dst.fileno()
    #copiamos el archivo
    await aiofiles.os.sendfile(fd_dst, fd_src, 0 , n_bytes) # no funciona porque el estandar de os en windows no lo tiene
"""
asyncio.run(main())