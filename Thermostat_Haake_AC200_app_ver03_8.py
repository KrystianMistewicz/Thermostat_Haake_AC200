
import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import messagebox


class app():
    def __init__(self, version):
        self.version = version
        self.serial_port = None
        self.current_temperature = None
        self.root = tk.Tk()
        self.main_frame = tk.Frame(self.root)
        self.current_temp_indicator = None
        self.program_indicator = None
        self.font1 = 'Arial 16 bold'
        self.font2 = 'Arial 20 bold'
        self.T1 = None
        self.T2 = None
        self.T_step = None
        self.t_int = None
        self.temperature_to_set = None
        self.steps_number = 0
        self.current_step = 0
        self.cooling = False

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def read_current_temp(self):
        command = "RT\r"
        interval = 5000 # Interval time in [ms] between temperature measurement
        self.serial_port.write(command.encode())
        current_temperature = self.serial_port.readline()
        text = str(current_temperature)
        current_temp = text[2:7]
        self.current_temp_indicator.configure(text=current_temp)
        self.root.after(interval, self.read_current_temp)

    def str_to_float_conversion(self, text):
        try:
            float(text)
            conversion_successful = True
        except ValueError:
            conversion_successful = False
        return conversion_successful

    def connect_to_device(self, serial_name):
        try:
            self.serial_port = serial.Serial(serial_name, baudrate=19200, bytesize=8, timeout=1)
            messagebox.showinfo(title='Device connected', message='Device was connected successfully.')
            self.clear_main_frame()
            self.create_temperature_monitor()
        except serial.SerialException:
            messagebox.showerror(title='Error', message='Device was not connected. Try again.')

    def create_main_window(self):
        self.root.title('App for thermostat Haake AC200 by Krystian Mistewicz (version %s)' % str(self.version))
        self.root.iconbitmap('icon.ico')
        self.root.state('zoomed')
        window_width = self.root.winfo_screenwidth()
        window_height = self.root.winfo_screenheight()
        self.root.geometry('%ix%i' % (window_width, window_height))
        self.main_frame.pack()
        canvas1 = tk.Canvas(self.main_frame, width=window_width, height=10)
        canvas1.pack()
        canvas1.create_line(0, 5, window_width, 5, width=2)
        label1 = tk.Label(self.main_frame, text='\nThe names of available serial ports:', font=self.font1)
        label1.pack()
        ports_lists = serial.tools.list_ports.comports()
        # print(ports_lists)
        text = ''
        if len(ports_lists) == 0:
            text = 'Connect device to PC !\n'
            label2 = tk.Label(self.main_frame, text=text, fg='red', font=self.font1)
        else:
            for item in ports_lists:
                text = text + str(item.device) + '\n'
                # print(item.device)
            label2 = tk.Label(self.main_frame, text=text, fg='RoyalBlue4', font=self.font1)
        label2.pack()
        canvas2 = tk.Canvas(self.main_frame, width=window_width, height=10)
        canvas2.pack()
        canvas2.create_line(0, 5, window_width, 5, width=2)
        label3 = tk.Label(self.main_frame, text='\n\nInsert name of the device serial port:\n', font=self.font1)
        label3.pack()
        serial_name_entry = tk.Entry(self.main_frame, width=10, bg='lightgrey', font=self.font1, justify='center')
        serial_name_entry.pack()
        label4 = tk.Label(self.main_frame, text='\n', font=self.font1)
        label4.pack()
        connect_button = tk.Button(self.main_frame, text='CONNECT DEVICE', font=self.font2, bg='lightgrey', width=15, height=1, command=lambda:self.connect_to_device(serial_name_entry.get()))
        connect_button.pack()
        label5 = tk.Label(self.main_frame, text='\n', font=self.font1)
        label5.pack()
        canvas3 = tk.Canvas(self.main_frame, width=window_width, height=10)
        canvas3.pack()
        canvas3.create_line(0, 5, window_width, 5, width=2)
        self.root.mainloop()

    def set_constant_temp(self, entry):
        if self.str_to_float_conversion(entry):
            # command_example = "SS 28.00\r"
            command = "SS %2.2f\r" % float(entry)
            try:
                self.serial_port.write(command.encode())
                messagebox.showinfo(title='Constant temperature', message='The temperature was set to %2.2f C deg.' % float(entry))
                self.program_indicator.configure(text='\nActive program: constant temperature T = %2.1f C deg.' % float(entry), fg='red')
            except serial.SerialException:
                messagebox.showerror(title='Error', message='Something went wrong. Temperature was not set. Try again.')
        else:
            messagebox.showerror(title='Error', message='You inserted wrong data. Try again.')

    def stepped_tem_ramping(self):
        safety_bufor = 0.001
        condition1 = not self.cooling and (self.temperature_to_set <= (self.T2 + safety_bufor))
        condition2 = self.cooling and (self.temperature_to_set >= (self.T2 - safety_bufor))
        continue_condition = condition1 or condition2
        if continue_condition:
            command = "SS %2.2f\r" % self.temperature_to_set
            try:
                self.serial_port.write(command.encode())
            except serial.SerialException:
                messagebox.showerror(title='Error', message='Something went wrong.')
                return
            # print(self.T_step)
            # print(self.temperature_to_set)
            self.current_step += 1
            self.program_indicator.configure(text='\nActive program: stepped temperature ramping\nfrom %2.1f C deg. to %2.1f C deg. with step of %2.1f C deg. and time interval of %2.0f sec.\nStep: %i of %i   Set temperature: T = %2.1f C deg.' % (self.T1, self.T2, self.T_step, self.t_int, self.current_step, self.steps_number, self.temperature_to_set), fg='red')
            self.temperature_to_set += self.T_step
            self.root.after(int(1000*self.t_int), self.stepped_tem_ramping)

    def set_stepped_temp(self, entry1, entry2, entry3, entry4):
        # entry1, entry2, entry3, entry4 correspond to entries of T_initial, T_final, T_step, t_interval
        if self.str_to_float_conversion(entry1) and self.str_to_float_conversion(entry2) and self.str_to_float_conversion(entry3) and self.str_to_float_conversion(entry4):
            self.T1 = float(entry1)
            self.T2 = float(entry2)
            self.T_step = float(entry3)
            self.t_int = float(entry4)
            messagebox.showinfo(title='Stepped temperature ramping set', message='Stepped temperature ramping was set.')
            self.program_indicator.configure(text='\nActive program: stepped temperature ramping\nfrom %2.1f C deg. to %2.1f C deg. with step of %2.1f C deg. and time interval of %2.0f sec.' % (self.T1, self.T2, self.T_step, self.t_int), fg='red')
            self.temperature_to_set = self.T1
            self.steps_number = int(abs(self.T2 - self.T1) / self.T_step) + 1
            if self.T2 < self.T1:
                self.cooling = True
                self.T_step = - abs(self.T_step)
            self.current_step = 0
            self.stepped_tem_ramping()
        else:
            messagebox.showerror(title='Error', message='You inserted wrong data. Try again.')

    def create_temperature_monitor(self):
        window_width = self.root.winfo_screenwidth()
        label1 = tk.Label(self.main_frame, text='\n', font='Arial 8')
        label1.pack()
        canvas1 = tk.Canvas(self.main_frame, width=window_width, height=10)
        canvas1.pack()
        canvas1.create_line(0, 5, window_width, 5, width=2)
        label2 = tk.Label(self.main_frame, text='\nCurrent temperature [C deg.]', font=self.font1)
        label2.pack()
        self.current_temp_indicator = tk.Label(self.main_frame, text='', font=self.font2)
        self.current_temp_indicator.pack()
        self.read_current_temp()
        label3 = tk.Label(self.main_frame, text='', font=self.font2)
        label3.pack()
        canvas2 = tk.Canvas(self.main_frame, width=window_width, height=10)
        canvas2.pack()
        canvas2.create_line(0, 5, window_width, 5, width=2)
        label4 = tk.Label(self.main_frame, text='\nSet constant temperature [C deg.]\n', font=self.font1)
        label4.pack()
        constant_temp_entry = tk.Entry(self.main_frame, width=6, bg='lightgrey', font=self.font2, justify='center')
        constant_temp_entry.pack()
        label5 = tk.Label(self.main_frame, text='\n', font='Arial 8')
        label5.pack()
        set_constant_button = tk.Button(self.main_frame, text='SET', font=self.font2, bg='lightgrey', width=8, height=1, command=lambda:self.set_constant_temp(constant_temp_entry.get()))
        set_constant_button.pack()
        label6 = tk.Label(self.main_frame, text='', font=self.font2)
        label6.pack()
        canvas3 = tk.Canvas(self.main_frame, width=window_width, height=10)
        canvas3.pack()
        canvas3.create_line(0, 5, window_width, 5, width=2)
        label7 = tk.Label(self.main_frame, text='\nSet stepped temperature ramping\n', font=self.font1)
        label7.pack()
        frame1 = tk.Frame(self.root)
        frame1.pack()
        label8 = tk.Label(frame1, text='T initial [C deg.]:', font=self.font1)
        label8.grid(row=0, column=0)
        initial_temp_entry = tk.Entry(frame1, width=6, bg='lightgrey', font=self.font2, justify='center')
        initial_temp_entry.grid(row=0, column=1)
        label9 = tk.Label(frame1, text='', font=self.font1, width=4)
        label9.grid(row=0, column=2)
        label10 = tk.Label(frame1, text='T final [C deg.]:', font=self.font1)
        label10.grid(row=0, column=3)
        final_temp_entry = tk.Entry(frame1, width=6, bg='lightgrey', font=self.font2, justify='center')
        final_temp_entry.grid(row=0, column=4)
        label11 = tk.Label(frame1, text='', font=self.font1, width=4)
        label11.grid(row=0, column=5)
        label12 = tk.Label(frame1, text='T step [C deg.]:', font=self.font1)
        label12.grid(row=0, column=6)
        step_temp_entry = tk.Entry(frame1, width=6, bg='lightgrey', font=self.font2, justify='center')
        step_temp_entry.grid(row=0, column=7)
        label13 = tk.Label(frame1, text='', font=self.font1, width=4)
        label13.grid(row=0, column=8)
        label14 = tk.Label(frame1, text='time interval [sec.]:', font=self.font1)
        label14.grid(row=0, column=9)
        time_interval_entry = tk.Entry(frame1, width=6, bg='lightgrey', font=self.font2, justify='center')
        time_interval_entry.grid(row=0, column=10)
        frame2 = tk.Frame(self.root)
        frame2.pack()
        label15 = tk.Label(frame2, text='\n', font='Arial 8')
        label15.pack()
        set_stepped_ramping_button = tk.Button(frame2, text='SET', font=self.font2, bg='lightgrey', width=8, height=1, command=lambda:self.set_stepped_temp(initial_temp_entry.get(), final_temp_entry.get(), step_temp_entry.get(), time_interval_entry.get()))
        set_stepped_ramping_button.pack()
        label16 = tk.Label(frame2, text='', font=self.font2)
        label16.pack()
        canvas3 = tk.Canvas(frame2, width=window_width, height=10)
        canvas3.pack()
        canvas3.create_line(0, 5, window_width, 5, width=2)
        self.program_indicator = tk.Label(frame2, text='\nActive program: not selected', fg='grey', font=self.font1)
        self.program_indicator.pack()


# serial_port.close()

app_version = 3.8

if __name__ == '__main__':
    app = app(app_version)
    app.create_main_window()