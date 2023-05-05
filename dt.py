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
from functools import partial
from kivy.lang import Builder


import requests
from bs4 import BeautifulSoup
import time
import sqlite3
import copy
import smtplib
from email.mime.text import MIMEText
from smtplib import SMTP

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



class InputWindow(BoxLayout):
    def __init__(self, app, **kwargs):
        super(InputWindow, self).__init__(**kwargs)
        self.app = app
        self.orientation = "vertical"
        self.spacing = 10
        self.padding = [20, 10]

        self.label_alue = Label(text="Kirjoita alue:", size_hint=(1, None), height=30, halign="left")
        self.textinput_alue = TextInput(multiline=False, size_hint=(1, None), height=30)
        self.textinput_alue.background_color = get_color_from_hex("#E0E0E0")  # Gray background color

        self.label_hakusana = Label(text="Kirjoita yksi hakusana:", size_hint=(1, None), height=30, halign="left")
        self.textinput_hakusana = TextInput(multiline=False, size_hint=(1, None), height=30)
        self.textinput_hakusana.background_color = get_color_from_hex("#E0E0E0")  # Gray background color

        self.button_submit = Button(text="Hae töitä", size_hint=(0.5, None), height=30, on_release=self.submit)
        self.button_submit.background_color = get_color_from_hex("#4287f5")  # Blue background color
        self.button_submit.color = [1, 1, 1, 1]

        self.add_widget(self.label_alue)
        self.add_widget(self.textinput_alue)
        self.add_widget(self.label_hakusana)
        self.add_widget(self.textinput_hakusana)
        self.add_widget(self.button_submit)

        with self.canvas.before:
            Color(0.3, 0.3, 0.3, 1)  # Light gray background color
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def submit(self, instance):
        alue = self.textinput_alue.text
        hakusana = self.textinput_hakusana.text

        if not alue.isalpha() or not hakusana.isalpha():
            print("Virheellinen syöte. Anna vain merkkijonoja.")
        else:
            self.app.switch_to_scroll_view(alue, hakusana)
        
class ScrollViewWindow(BoxLayout):
    def __init__(self, **kwargs):
        super(ScrollViewWindow, self).__init__(**kwargs)
        self.orientation = "vertical"

        with self.canvas.before:
            Color(0.1, 0.1, 0.1, 1)  # White background color
        self.rect = Rectangle(pos=self.pos, size=self.size)
        self.top_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))  # Top layout for progress bar
        self.progress_bar = ProgressBar(max=1.0, size_hint=(1, 1))  # Progress bar instance
        self.top_layout.add_widget(self.progress_bar)  # Add progress bar to top layout
        self.bind(pos=self.update_rect, size=self.update_rect)
        self.scroll_view = ScrollView(do_scroll_x=False, do_scroll_y=True)
        self.label = Label(size_hint=(1, None), text_size=(None, None), valign='top')
        self.label.bind(texture_size=self.label.setter('size'))
        self.scroll_view.add_widget(self.label)
        self.progress_bar = None  # Initialize the ProgressBar wi
        self.add_widget(self.scroll_view)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def update_label_text(self, text, dt=None):
        self.label.text += text + "\n"

    def reset_label_text(self):
        self.label.text = ""

    def remove_progress_bar(self):
        if self.progress_bar is not None:  # If the ProgressBar widget exists
            self.remove_widget(self.progress_bar)  # Remove it from the layout
            self.progress_bar = None  # Reset the reference to the Progress
                
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
    
            
    def get(self, alue, hakusana):
        nr = 1
        self.paikka_copies = []
        progress_bar = ProgressBar(max=100)  # Adjust the max value as needed
        self.scroll_view_window.add_widget(progress_bar)
        
        def update_progress(dt):
            nonlocal nr
            url = f'https://duunitori.fi/tyopaikat/{alue}/{hakusana}?sivu={nr}'
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            job_listings = soup.find_all('div', class_='grid grid--middle job-box job-box--lg')

            try:
                sivunr = soup.select_one('.pagination__splitted a:last-child')
                sivunr = int(sivunr.text)
            except:
                sivunr = 1

            # Check if a progress bar already exists
            if not any(isinstance(widget, ProgressBar) for widget in self.scroll_view_window.children):
                # Create a new progress bar if one does not already exist
                progress_bar = ProgressBar(max=100, size_hint_y=0.05)  # Adjust the max value as needed
                self.scroll_view_window.add_widget(progress_bar)
            else:
                # Update the existing progress bar if one already exists
                progress_bar = next(widget for widget in self.scroll_view_window.children if isinstance(widget, ProgressBar))
            
            
            progress_value = int(nr / sivunr * 100)  # Calculate progress value
            progress_bar.value = progress_value  # Update the progress bar value
            
            for job in job_listings:
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

            
            if nr >= sivunr:
                self.new_jobs = self.paikka_copies
                self.switch_to_scroll_view(alue, hakusana)
                Clock.unschedule(update_progress)  # Stop the interval from running when progress is complete
            else:
                nr += 1
        
        #Clock.schedule_interval(update_progress, 1) 
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

        


    
