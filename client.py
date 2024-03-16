import socket
import cv2
import pickle
import struct
import threading
import pyaudio
import ssl
import os

host_ip = 'IP_address'
port_video = 9998
port_audio = 9996

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

server_sni_hostname = 'example.com'
server_cert = 'server.crt'
client_cert = 'client.crt'
client_key = 'client.key'

context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=server_cert)
context.load_cert_chain(certfile=client_cert, keyfile=client_key)

def handle_server_video(client_socket):
    data = b""
    payload_size = struct.calcsize("Q")
    print("Connected to server successfully!!")
    while True:
        try:
            while len(data) < payload_size:
                packet = client_socket.recv(4*1024)
                if not packet: break
                data += packet
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]

            while len(data) < msg_size:
                data += client_socket.recv(4*1024)
            frame_data = data[:msg_size]
            data = data[msg_size:]

            # Extract frame
            frame = pickle.loads(frame_data)

            # Display frame in a window
            # 
            cv2.imshow("RECEIVING VIDEO", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                os._exit(0)
                # break
        except struct.error:
            print("Server disconnected")
            os._exit(0)
            break


def handle_server_audio(client_socket):
    
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True,
                    frames_per_buffer=CHUNK)
    try:
        while True:
            audio_data = client_socket.recv(CHUNK)
            stream.write(audio_data)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

def main():
    client_socket_video = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket_video.connect((host_ip, port_video))

    client_socket_audio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket_audio.connect((host_ip, port_audio))

    video_thread = threading.Thread(target=handle_server_video, args=(client_socket_video,))
    video_thread.start()

    audio_thread = threading.Thread(target=handle_server_audio, args=(client_socket_audio,))
    audio_thread.start()

if __name__ == "__main__":
    main()