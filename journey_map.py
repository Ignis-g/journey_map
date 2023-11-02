import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
from ReadWriteMemory import ReadWriteMemory
from struct import unpack

# Constants
WAYFARER_COLOR = 'cyan'
NICK_COLOR = 'red'
PEN_SIZE = 8

# TODO: Finding the min and max on all maps. Eventually making arrows for the corners as well. 
LEVELS = {
    0: {'image_name': '01_Chapter_Select_CS_map.webp', 'x': 1843.2, 'x_min': -63, 'x_max': 575, 'z': 409.6, 'z_min': -125, 'z_max': 1151, 'step': 3.2},
    1: {'image_name': '02_Broken_Bridge_BB_map.webp',  'x': 1843.2, 'z': 409.6, 'step': 3.2},
    2: {'image_name': '03_Pink_Desert_PD_map.webp',    'x': 1843.2, 'z': 409.6, 'step': 3.2},
    3: {'image_name': '04_Sunken_City_SC_map.webp',    'x': 1785,   'z': 521.8, 'step': 2.98},
    4: {'image_name': '05_Underground_UG_map.webp',    'x': 1843.2, 'z': 253.1, 'step': 3.2},
    5: {'image_name': '06_Tower_map.webp',             'x': 1843.2, 'z': 409.6, 'step': 3.2, 'y_minimap': 1140, 'z_minimap': -1320},
    6: {'image_name': '07_Snow_map.webp',              'x': 1843.2, 'z': 409.6, 'step': 3.2},
    7: {'image_name': '08_Paradise_map.webp',          'x': 1660,   'z': 775.9, 'step': 2.48},
}

POSITION_POINTER_ADDR = 0x3C47B18

WAYFARER_POINTER_OFFSETS = [
    [0x60, 0x28, 0xD0, 0x100, 0x30, 0x370, 0xC0],
    [0x70, 0x178, 0x78, 0xD0, 0x108, 0x3A8, 0xC4],
    [0x70, 0x28, 0xD0, 0x108, 0x30, 0x370, 0xC8]
]

NICK_POINTER_OFFSETS = [
    [0x60, 0x28, 0xD0, 0x108, 0x4A0, 0x10, 0x948],
    [0x60, 0x28, 0xD0, 0x108, 0x4A0, 0x10, 0x94C],
    [0x60, 0x28, 0xD0, 0x108, 0x4A0, 0x10, 0x950]
]

LEVEL_POINTER_ADDR = 0x3CFCA80

LEVEL_POINTER_OFFSETS = [0x70, 0x28, 0xD0, 0x100, 0x30, 0x368, 0x30]

class JourneyTrackerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Journey")
        #self.window_size = (self.root.winfo_screenwidth(), self.root.winfo_screenheight())
        self.window_size = (1000, 500)
        self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}")
        #self.root.state('zoomed')
                
        self.process = None
        self.image = None
        self.current_level_id = 0

        self.create_gui()
        self.load_image()
        self.updateProcess() 
        self.update()

    def create_gui(self):
        empty_image = tk.PhotoImage(width=1, height=1)
        self.img_label = tk.Label(self.root, image=empty_image)
        self.img_label.pack(fill=tk.BOTH, expand=True)
        self.root.bind("<Configure>", self.resize_canvas)

    def load_image(self):
        try:
            image = Image.open(LEVELS.get(self.current_level_id, {}).get('image_name', 'Unknown_map.webp'))
            image_resized = ImageTk.PhotoImage(image.resize((self.window_size[0], self.window_size[1]), Image.LANCZOS))
            self.img_label.config(image=image_resized)
            self.img_label.image = image_resized
            self.image = image
        except Exception as e:
            print(f"Error loading image: {e}")

    def load_dot_coordinates(self):
        def read_coordinates(addresses):
            position = []
            
            for address in addresses:
                position.append(unpack('<f', self.process.read(address).to_bytes(4, 'little'))[0])
            
            return tuple(position)

        return [read_coordinates(self.wayfarer_pos_addresses), read_coordinates(self.nick_pos_addresses)]

    def draw_dots(self):
        def in_boundaries(position):
            return 470 < position < 850
        
        if self.image is None:
            return

        image_draw = self.image.copy()
        draw = ImageDraw.Draw(image_draw)
        coordinates = self.load_dot_coordinates()

        level_data = LEVELS.get(self.current_level_id, {})
        x_origin = level_data.get('x', 1843.2)
        x_min, x_max = level_data.get('x_min', -63), level_data.get('x_max', 575)
        z_origin = level_data.get('z', 409.6)
        z_min, z_max = level_data.get('z_min', -125), level_data.get('z_max', 1151)
        step = level_data.get('step', 3.2)

        for (x, y, z), color in [(coordinates[0], WAYFARER_COLOR), (coordinates[1], NICK_COLOR)]:
            if z < z_min:
                draw.polygon([(z_origin + z_min * step, x_origin - x * step),
                              (z_origin + z_min * step + PEN_SIZE * 2, x_origin - x * step - PEN_SIZE * 2),
                              (z_origin + z_min * step + PEN_SIZE * 2, x_origin - x * step + PEN_SIZE * 2)], fill=color)
            elif z > z_max:
                draw.polygon([(z_origin + z_max * step, x_origin - x * step),
                              (z_origin + z_max * step - PEN_SIZE * 2, x_origin - x * step - PEN_SIZE * 2),
                              (z_origin + z_max * step - PEN_SIZE * 2, x_origin - x * step + PEN_SIZE * 2)], fill=color)
            elif x < x_min:
                draw.polygon([(z_origin + z * step, x_origin - x_min * step),
                              (z_origin + z * step - PEN_SIZE * 2, x_origin - x_min * step - PEN_SIZE * 2),
                              (z_origin + z * step + PEN_SIZE * 2, x_origin - x_min * step - PEN_SIZE * 2)], fill=color)
            elif x > x_max:
                draw.polygon([(z_origin + z * step, x_origin - x_max * step),
                              (z_origin + z * step - PEN_SIZE * 2, x_origin - x_max * step + PEN_SIZE * 2),
                              (z_origin + z * step + PEN_SIZE * 2, x_origin - x_max * step + PEN_SIZE * 2)], fill=color)
            else:
                draw.ellipse((z_origin + z * step - PEN_SIZE, x_origin - x * step - PEN_SIZE,
                              z_origin + z * step + PEN_SIZE, x_origin - x * step + PEN_SIZE), fill=color)

        if self.current_level_id == 5:
            y_minimap = level_data.get('y_minimap', 1500)
            z_minimap = level_data.get('z_minimap', 410)
            
            for (x, y, z), color in [(coordinates[0], WAYFARER_COLOR), (coordinates[1], NICK_COLOR)]:
                if in_boundaries(z):
                    draw.ellipse((z_minimap + z * step - PEN_SIZE, y_minimap - y * step - PEN_SIZE,
                                  z_minimap + z * step + PEN_SIZE, y_minimap - y * step + PEN_SIZE), fill=color)

        image_resized = ImageTk.PhotoImage(image_draw.resize((self.window_size[0], self.window_size[1]), Image.LANCZOS))
        self.img_label.config(image=image_resized)
        self.img_label.image = image_resized

    def resize_canvas(self, event):
        width = event.width
        height = event.height

        if (width, height) != self.window_size:
            self.window_size = (width, height)

    def update(self):
        if self.process:
            new_level_id = self.process.read(self.level_id_pointer)
            if new_level_id != self.current_level_id:
                self.current_level_id = new_level_id
                self.load_image()

            self.draw_dots()
        self.root.after(100, self.update)

    def updateProcess(self):
        try:
            new_process = ReadWriteMemory().get_process_by_name('Journey.exe')
            if self.process != new_process:
                if self.process != None:
                    self.process.close()
                self.process = new_process
                self.process.open()
                self.base_address = self.process.get_base_address()
                self.level_id_pointer = self.process.get_pointer(self.base_address + LEVEL_POINTER_ADDR, offsets=LEVEL_POINTER_OFFSETS)

                self.wayfarer_pos_addresses = []
                for offset in WAYFARER_POINTER_OFFSETS:
                    self.wayfarer_pos_addresses.append(self.process.get_pointer(self.base_address + POSITION_POINTER_ADDR, offsets=offset))

                self.nick_pos_addresses = []
                for offset in NICK_POINTER_OFFSETS:
                    self.nick_pos_addresses.append(self.process.get_pointer(self.base_address + POSITION_POINTER_ADDR, offsets=offset))

        except Exception as e:
            print(f"Journey process not found.")
        self.root.after(5000, self.updateProcess)
        
    def run(self):
        self.root.mainloop()

    def close(self):
        if self.process:
            self.process.close()

if __name__ == "__main__":
    app = JourneyTrackerApp()
    app.run()
    app.close()
