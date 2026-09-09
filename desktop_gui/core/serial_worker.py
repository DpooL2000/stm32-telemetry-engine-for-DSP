import serial
import struct
import threading

class SerialLink:
    def __init__(self, port, baudrate, data_x, data_y, data_z, latest_angles):
        self.serial_port = serial.Serial(port, baudrate, timeout=0)
        self.serial_running = True
        
        # References to the main thread's data arrays
        self.data_x = data_x
        self.data_y = data_y
        self.data_z = data_z
        self.latest_angles = latest_angles
        
        self.STRUCT_FORMAT = '<IIfffffffff'
        self.STRUCT_SIZE = struct.calcsize(self.STRUCT_FORMAT)
        self.SYNC_WORD = 0xDDBBCCAA
        
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def send_command(self, cmd_string):
        self.serial_port.write(cmd_string.encode('ascii'))

    def _read_loop(self):
        buffer = bytearray()
        while self.serial_running:
            if self.serial_port.in_waiting:
                buffer.extend(self.serial_port.read(self.serial_port.in_waiting))
                while len(buffer) >= self.STRUCT_SIZE:
                    sync_val, = struct.unpack('<I', buffer[0:4])
                    if sync_val == self.SYNC_WORD:
                        data = struct.unpack(self.STRUCT_FORMAT, buffer[:self.STRUCT_SIZE])
                        
                        self.data_x.append(data[2])  # Gyro X
                        self.data_y.append(data[3])  # Gyro Y
                        self.data_z.append(data[4])  # Gyro Z
                        
                        # Update angles: Roll, Pitch, Yaw
                        self.latest_angles[0] = data[8]
                        self.latest_angles[1] = data[9]
                        self.latest_angles[2] = data[10]
                        
                        del buffer[:self.STRUCT_SIZE]
                    else:
                        del buffer[0:1]

    def close(self):
        self.serial_running = False
        self.serial_port.close()
