from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.progressbar import ProgressBar
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import get_color_from_hex
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.properties import NumericProperty



from functools import partial
import threading
from threading import Thread

import requests
from bs4 import BeautifulSoup
import time
import sqlite3
import copy
import smtplib
from email.mime.text import MIMEText
from smtplib import SMTP
from kivy.metrics import dp


# Establish a connection to the database
conn = sqlite3.connect('jobs.db')
cursor = conn.cursor()

# Create a table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        job_url TEXT
    )
''')
conn.commit()


##class TestSMTP(SMTP):
##    def __init__(self, host='localhost', port=25, local_hostname=None,
##                 timeout=60, source_address=None):
##        super().__init__(host, port, local_hostname, timeout, source_address)
##        self.debuglevel = 1  # Enable debug output
##
##    def send_message(self, msg, from_addr=None, to_addrs=None, mail_options=(),
##                     rcpt_options=()):
##        # Instead of sending the message, print it to the console
##        print(msg)
##
##        
##def send_email(recipient, subject, message):
##    sender = 'your_email@example.com'
##    password = 'your_email_password'
##    smtp_server = 'localhost'
##    smtp_port = 25
##
##    msg = MIMEText(message)
##    msg['Subject'] = subject
##    msg['From'] = sender
##    msg['To'] = recipient
##
##    with TestSMTP(smtp_server, smtp_port) as server:
##        server.login(sender, password)
##        server.send_message(msg)
class MyProgressBar(ProgressBar):
    def __init__(self, **kwargs):
        super(MyProgressBar, self).__init__(**kwargs)
        self.value = 0
        self.max = 100
        self.increment = 1

    def start(self):
        self.event = threading.Event()
        self.event.set()
        self.is_running = True
        self.value = 0
        self.event = Clock.schedule_interval(self.update,0.1)

    def update(self, dt=None):
        self.value += self.increment
        if self.value >= self.max:
            self.stop()

    def stop(self):
        self.is_running = False
        if hasattr(self, 'event'):
            self.value = 100
            Clock.unschedule(self.event)
        
    def reset(self):
        self.value = 0
        self.event = Clock.schedule_once(self.update, 1)


class InputWindow(BoxLayout):
    def __init__(self, app, **kwargs):
        super(InputWindow, self).__init__(**kwargs)
        self.app = app
        self.orientation = "vertical"
        self.spacing = dp(10)
        self.padding = [dp(20), dp(10)]

        # Create the widgets
        self.label_alue = Label(text="Kirjoita alue:", size_hint=(None, None), size=(dp(250), dp(30)), height=dp(30), halign="left", pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.textinput_alue = TextInput(multiline=False, size_hint=(None, None),size=(dp(300), dp(30)), height=dp(30), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.textinput_alue.background_color = get_color_from_hex("#E0E0E0")  # Gray background color

        self.label_hakusana = Label(text="Kirjoita yksi hakusana:", size_hint=(None , None), size=(dp(250), dp(30)), height=dp(30), halign="left", pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.textinput_hakusana = TextInput(multiline=False, size_hint=(None, None),size=(dp(300), dp(30)), height=dp(30), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.textinput_hakusana.background_color = get_color_from_hex("#E0E0E0")  # Gray background color

        self.button_submit = Button(text="Hae töitä", size_hint=(0.15, None), height=dp(30), on_release=self.submit, pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.button_submit.background_color = get_color_from_hex("#4287f5")  # Blue background color
        self.button_submit.color = [1, 1, 1, 1]

        self.label_luku = Label(text="", size_hint=(None, None), size=(dp(20), dp(30)))
        
        self.progress_bar = MyProgressBar(size_hint=(0.5, None), size=(dp(250), dp(20)), height=dp(20), center_x=self.width/2)
        spacer = Label(text='', size_hint=(None, None), size=(dp(30), dp(1)))
       # spacer2 = Label(text='', size_hint=(None, None), size=(dp(240), dp(1)))


        # Add the widgets to the layout
        layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(30))

      #  layout.add_widget(spacer2)
        layout.add_widget(self.progress_bar)
        layout.add_widget(spacer)
        layout.add_widget(self.label_luku)

        self.add_widget(self.label_alue)
        self.add_widget(self.textinput_alue)
        self.add_widget(self.label_hakusana)
        self.add_widget(self.textinput_hakusana)
        self.add_widget(self.button_submit)
        self.add_widget(layout)

        # Position the label_luku widget to the right of the progress_bar widget
        self.label_luku.pos_hint = {'right': self.progress_bar.right}

        with self.canvas.before:
            Color(0.3, 0.3, 0.3, 1)  # Light gray background color
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        

    def submit_with_progress_bar(self, alue:str, hakusana:str):
        print("submit_with_progress_bar called")
        
        self.app.switch_to_scroll_view(alue, hakusana)

    # modify your submit method to call the new function with threading
    def submit(self, instance):
        alue = self.textinput_alue.text
        hakusana = self.textinput_hakusana.text
        if not alue.isalpha() or not hakusana.isalpha():
            print("Virheellinen syöte. Anna vain merkkijonoja.")
        else:
            print("Before starting thread")
            threading.Thread(target=self.submit_with_progress_bar, args=(alue, hakusana)).start()
            print("After starting thread")   


         
class ScrollViewWindow(BoxLayout):
    def __init__(self, **kwargs):
        super(ScrollViewWindow, self).__init__(**kwargs)
        self.orientation = "vertical"

        with self.canvas.before:
            Color(0.1, 0.1, 0.1, 1)  # White background color
        self.rect = Rectangle(pos=self.pos, size=self.size)
        self.top_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))  # Top layout for progress bar
        self.bind(pos=self.update_rect, size=self.update_rect)
        self.scroll_view = ScrollView(do_scroll_x=False, do_scroll_y=True)
        self.label = Label(size_hint=(1, None), text_size=(None, None), valign='top')
        self.label.bind(texture_size=self.label.setter('size'))
        self.scroll_view.add_widget(self.label)
        self.add_widget(self.scroll_view)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def update_label_text(self, text, dt=None):
        self.label.text += text + "\n"

    def reset_label_text(self):
        self.label.text = ""

                
class MyApp(App):
    def __init__(self, **kwargs):
        super(MyApp, self).__init__(**kwargs)
        self.input_window = InputWindow(self)
        self.scroll_view_window = ScrollViewWindow()
        self.window_manager = BoxLayout(orientation="vertical")
        self.window_manager.add_widget(self.input_window)
        self.window_manager.add_widget(self.scroll_view_window)
        self.paikka_copies = []


        
    def build(self):
        return self.window_manager

    def switch_to_scroll_view(self, alue, hakusana):
        self.new_jobs = self.lahetys(alue, hakusana)  # Store new_jobs as an instance variable
        text = ""

        if self.new_jobs:
            for job in self.new_jobs:
                text += f'Title: {job[0]}\nCompany: {job[1]}\nJob URL: {job[2]}\n\n'
        else:
            text = "No new jobs"


        self.scroll_view_window.reset_label_text()  # Reset the label text
        
        for widget in self.scroll_view_window.children:
            if isinstance(widget, ProgressBar):
                self.scroll_view_window.remove_widget(widget)
                
        
        self.scroll_view_window.update_label_text(text)  # Update with new text
        self.window_manager.current = "scroll_view"

    def get_database(self):
        conn = sqlite3.connect('jobs.db')
        cursor = conn.cursor()
        cursor.execute("SELECT title, company, job_url FROM jobs")
        rows = cursor.fetchall()
        result = [tuple(row) for row in rows]  # Convert rows to tuples
        return result
        
        


    def lahetys(self, alue, hakusana):

        data = self.get_database()  # Retrieve data from the database
        uusdata = self.get(alue, hakusana)
        new_jobs = []

        conn = sqlite3.connect('jobs.db')
        cursor = conn.cursor()

        for i in range(0, len(uusdata), 3):
            title, firma, href = uusdata[i:i+3]  # Unpack the values from uusdata
            
            if (title, firma, href) not in [tuple(item) for item in data]:  # Convert data to tuples for comparison
                cursor.execute('INSERT INTO jobs (title, company, job_url) VALUES (?, ?, ?)', (title, firma, href))
                conn.commit()
                new_jobs.append((title, firma, href))
        
        conn.close()
        return new_jobs
    



        
    def fetch_jobs(self, alue:str, hakusana:str, nr:int):
        url = f'https://duunitori.fi/tyopaikat/{alue}/{hakusana}?sivu={nr}'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        job_listings = soup.find_all('div', class_='grid grid--middle job-box job-box--lg')

        try:
            sivunr = soup.select_one('.pagination__splitted a:last-child')
            sivunr = int(sivunr.text)
        except:
            sivunr = 1

        print(nr,"/",sivunr)

        # Set the maximum value of the progress bar to the number of job listings
        self.input_window.progress_bar.max = len(job_listings)

        for i, job in enumerate(job_listings):
            paikka = []
            a_element = job.find('a', class_='job-box__hover gtm-search-result')
            if a_element:
                title = a_element.text
                firma = a_element["data-company"]
                href = a_element['href']

                paikka.append(title)
                paikka.append(firma)
                paikka.append(href)
                self.paikka_copies.extend(paikka)
            #self.input_window.progress_bar.start()
            # Update the progress bar value after each job listing is processed
        return sivunr


    def fetch_jobs_thread(self, alue, hakusana, nr):
        while True:
            sivunr = self.fetch_jobs(alue, hakusana, nr)
            nr += 1
            if nr > sivunr:
                break
            self.input_window.progress_bar.value = nr
            self.input_window.label_luku.text = str(f'Sivu: {nr}/{sivunr}')

        self.input_window.progress_bar.stop()

    def get(self, alue:str, hakusana:str):
        self.paikka_copies = []
        nr = 1
        sivunr = self.fetch_jobs(alue, hakusana, nr)
        self.input_window.progress_bar.reset()
        self.input_window.label_luku.text = str(f'Sivu: {nr}/{sivunr}')

        t1 = threading.Thread(target=self.fetch_jobs_thread, args=(alue, hakusana, nr))
        t1.start()
        while t1.is_alive():
            self.input_window.progress_bar.update()
            time.sleep(0.1)
        return self.paikka_copies


    
    ##    if new_jobs:
    ##        recipient = 'recipient_email@example.com'
    ##        subject = 'New Job Listings'
    ##        message = 'The following job listings are not in the database:\n\n'
    ##        for job in new_jobs:
    ##            message += f'Title: {job[0]}\nCompany: {job[1]}\nJob URL: {job[2]}\n\n'
    ##        send_email(recipient, subject, message)
    ##        print("sent")
    ##    else:
    ##        print("no new jobs")


    
if __name__ == "__main__":
    MyApp().run()

        


    
