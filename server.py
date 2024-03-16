import socket
import cv2
import pickle
import struct
import threading
import pyaudio
import ssl
import os

p = pyaudio.PyAudio()
vid = cv2.VideoCapture(0)
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

server_cert = 'server.crt'
server_key = 'server.key'
client_certs = 'client.crt'

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.verify_mode = ssl.CERT_REQUIRED
context.load_cert_chain(certfile=server_cert, keyfile=server_key)
context.load_verify_locations(cafile=client_certs)


def handle_client_video(client_socket):
    print("Got connection from", client_socket.getpeername())
    try:
        while vid.isOpened():
            img, frame = vid.read()
            if img:
                data = pickle.dumps(frame)
                message = struct.pack("Q", len(data)) + data
                client_socket.sendall(message)
    except ConnectionResetError:
        print("Client closed video connection")
    finally:
        client_socket.close()


def handle_client_audio(client_socket):
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    try:
        while True:
            audio_data = stream.read(CHUNK)
            client_socket.sendall(audio_data)
    except ConnectionResetError:
        print("Client closed audio connection")
    finally:
        stream.stop_stream()
        stream.close()
        client_socket.close()


def main():
    server_socket_video = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket_audio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_ip = 'IP_address'
    print('HOST IP:', host_ip)
    port_video = 9998
    port_audio = 9996
    socket_address_video = (host_ip, port_video)
    socket_address_audio = (host_ip, port_audio)

    server_socket_video.bind(socket_address_video)
    server_socket_video.listen(5)

    server_socket_audio.bind(socket_address_audio)
    server_socket_audio.listen(5)
    os.system('clear')
    print("LISTENING AT:", socket_address_video)
    print("LISTENING AT:", socket_address_audio)
    try:
        while True:
            client_socket_video, addr_video = server_socket_video.accept()
            client_socket_audio, addr_audio = server_socket_audio.accept()
            client_handler_video = threading.Thread(
                target=handle_client_video, args=(client_socket_video,))
            client_handler_video.start()
            client_handler_audio = threading.Thread(
                target=handle_client_audio, args=(client_socket_audio,))
            client_handler_audio.start()
    except KeyboardInterrupt:
        print("Server stopped")
        os._exit(0)


if __name__ == "__main__":
    main()