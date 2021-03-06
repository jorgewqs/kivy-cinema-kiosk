#This file is part of the Kivy Cinema Kiosk Demo.
#	Copyright (C) 2010 by 
#	Thomas Hansen  <thomas@kivy.org>
#	Mathieu Virbel <mat@kivy.org>
#
#	The Kivy Cinema Kiosk Demo is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	The Kivy Cinema Kiosk Demo is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with The Kivy Cinema Kiosk Demo.  If not, see <http://www.gnu.org/licenses/>.

# general imports ###################################################
import subprocess
import random
import shelve
from glob import glob

import threading
import socket
import struct
import json
import time

# kivy imports ######################################################
import kivy
kivy.require('1.0.4')

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.utils import get_color_from_hex

from kivy.core.audio import Sound
from kivy.core.image import ImageLoader
from kivy.core.video import Video as VideoBuffer
from kivy.graphics import *
from kivy.properties import *


from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.video import Video
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scatter import ScatterPlane, Scatter
from kivy.animation import Animation
from functools import partial





# local impots & globals ##############################################
#movies = shelve.open('movie.shelve')


class KivyWidgetMetaClass(type):  
	'''
	def __new__(cls, name, bases, attrs):  
		#replacement for original __init__ function
		original_init = attrs.get('__init__', bases[0].__init__)
		def alternate_init(self,*args,**kwargs):  
			original_init(self,*args,**kwargs)  
			if name == self.__class__.__name__: #dont call for each base class
				Clock.schedule_once(self.setup) #call setup next loop iteration
		attrs['__init__'] = alternate_init 
		return super(KivyWidgetMetaClass, cls).__new__(cls, name, bases, attrs)
	'''
	def __init__(self, name, bases, attrs):  
		super(KivyWidgetMetaClass, self).__init__(name, bases, attrs)
		Factory.register(name, self)
		#print "Registered %s in kivy Widget Factory" % name 




class Viewport(ScatterPlane):
	def __init__(self, **kwargs):
		kwargs['do_scale'] = False
		kwargs['do_rotation'] = False
		kwargs['do_translation'] = False
		kwargs['size_hint'] = (None, None)
		super(Viewport, self).__init__(**kwargs)

	def fit_to_window(self, *args):
		if Window.height > Window.width:
			self.scale = Window.width/float(self.width)
		else:
			self.scale = Window.height/float(self.width)
			self.rotation = 90
		self.pos = (0,0)
		#for sc in self.children:
		#	for s in sc.children:
		#		print s.__class__, s.size





class AppScreen(BoxLayout):
	app = ObjectProperty(None)

	def hide(self, *args):
		anim = Animation(x=-1080.0, t='out_quad')
		anim.start(self)

	def show(self, *args):
		self.x = 1080
		anim = Animation(x=0.0, t='out_quad')
		anim.start(self)



class InfoScreen(AppScreen):
	movie = ObjectProperty(None)

	def __init__(self, **kwargs):
		super(InfoScreen, self).__init__(**kwargs)
		self.fixed_layer = Widget(size_hint=(None, None), size=(0,0))
		self.add_widget(self.fixed_layer)

		self.video = Video(text="video", pos=(0,700), size=(1080, 920))
		self.video.volume = 1.0
		self.fixed_layer.add_widget(self.video)
		self.title_label = Label(text="TITLE", text_size=(1080,None), font_size=80, bold=True, pos=(0,410), halign='center', width=1080)
		self.fixed_layer.add_widget(self.title_label)
		self.movie = self.app.get_random_movie()
		#self.size = (1080,1921)
		self.size = (1080,1920)

		Clock.schedule_interval(self.video_eos_check,2.0 )

	def hide(self, *args):
		anim = Animation(x=-1280.0, t='out_quad')
		anim.start(self)
		anim.start(self.video)
		anim.start(self.title_label)
		self.video.play = False
		self.video._video.stop()

		subprocess.Popen('aplay -q content/hello.wav', shell=True)

	def show(self, *args):
		self.next_movie()
		self.x = 1080
		self.video.x = 1080
		self.title_label.x = 1080
		anim = Animation(x=0.0, t='out_quad',d=0.7)
		anim.start(self)
		anim.start(self.title_label)
		anim.start(self.video)
		self.app.set_logo_color(.2,.2,.2)



	def on_touch_up(self, touch):
		if self.collide_point(*touch.pos):
			self.app.goto(self.app.movie_screen)


	def video_eos_check(self, *args):
		#eos event not working for some reason
		#so check every two seconds, to force new movie...
		#print "CHEKCING FOR EOS:"
		#print self.video.source, self.video.eos
		if self.video.eos:
			self.next_movie()

	def next_movie(self, *args):
		current_movie = self.movie;
		while current_movie == self.movie:
			self.movie = self.app.get_random_movie();

	def play(self, *args):
		self.video.play = True


	def on_movie(self, *args):
		if not self.movie:
			return
		if len(self.movie.title) > 20:
			self.title_label.font_size = 60
		else:
			self.title_label.font_size = 80
		self.title_label.size = (1080, 400)
		self.title_label.text_size = (1080, 500)
		self.title_label.text = self.movie.title


		self.video.play = False
		self.video.eos = False
		self.video.source = ''
		self.video.source = self.movie.trailer
		Clock.schedule_once(self.play, 0.1)
		



class ThumbnailTitle(Label):
	pass
class ThumbnailDetails(Label):
	pass
class ThumbnailVideo(Image):
	pass

class MovieThumbnail(BoxLayout):
	movie = ObjectProperty(None)

	def __init__(self, **kwargs):
		super(MovieThumbnail, self).__init__(**kwargs)
		self.orientation = 'vertical'
		self.title = ThumbnailTitle(text='Movie Title')
		self.video = ThumbnailVideo()
		self.details = ThumbnailDetails(text='Movie Details')
		self.add_widget(self.title)
		self.add_widget(self.video)
		self.add_widget(Widget(size_hint=(1.0,0.2))) #padding
		self.add_widget(self.details)
		self.add_widget(Widget(size_hint=(1.0,0.8))) #padding

	def on_movie(self, *args):
		if not self.movie:
			return
		self.title.text = self.movie.title
		self.title.text_size = (250, None)
		self.details.text = self.movie.summary[:200]+'...'
		self.details.text_size = (300, None)


		self.video.source = self.movie.trailer.replace('.avi', '.png')
		#self.video.play = False
		#self.video._video.seek(2.0)
		#self.video.bind(on_eos=self.on_movie)
		#Clock.schedule_once(self.play,0.05)

	def play(self, *args):
		pass
		#self.video.volume = 0
		#self.video.play = True
		#self.video.volume = 0

	def on_touch_down(self, touch):
		if self.collide_point(*touch.pos):
			self.parent.parent.parent.parent.select_movie(self.movie)
			return True




class LogoImage(Image):
	bg_r = NumericProperty(.2)
	bg_g = NumericProperty(.2)
	bg_b = NumericProperty(.2)
	__metaclass__ = KivyWidgetMetaClass

	

class BuyButton(Button):
	
	pass
class BuyingOverlay(BoxLayout):
	num_adults = NumericProperty(2)
	num_kids = NumericProperty(0)

	def finish_buy(self, *args):
		self.parent.parent.finish_buy(*args)

	def decr_adults(self, *args):
		if self.num_adults > 0:
			self.num_adults -= 1

	def decr_kids(self, *args):
		if self.num_kids > 0:
			self.num_kids -= 1


class IncButton(Button):
	__metaclass__ = KivyWidgetMetaClass
class DecButton(Button):
	__metaclass__ = KivyWidgetMetaClass
class LeftButton(Button):
	__metaclass__ = KivyWidgetMetaClass
class RightButton(Button):
	__metaclass__ = KivyWidgetMetaClass
class MovieTitle(Label):
	pass
class MovieSummary(Label):
	pass
class MovieShowTimes(Video):
	pass
class MovieVideo(Video):
	pass
class MovieMetaInfo(Label):
	__metaclass__ = KivyWidgetMetaClass
	rating = StringProperty('PG-13')

class MovieScreen(AppScreen):
	'''MovieScreen, lets user select a movie, and see related movies
	'''
	def __init__(self, **kwargs):
		super(MovieScreen, self).__init__(**kwargs)

		self.movie = self.app.get_random_movie()

		self.fixed_layer = Widget()
		self.add_widget(self.fixed_layer)

		#video player
		self.video = MovieVideo(text="video", pos=(1080,1000), size=(1080, 920))
		self.video.volume = 1.0
		self.fixed_layer.add_widget(self.video)

		self.movie_title = MovieTitle(text='Movie Title', pos=(1080,780), width=1080)
		self.fixed_layer.add_widget(self.movie_title)

		self.movie_meta = MovieMetaInfo(rating="PG13", y=810)
		self.fixed_layer.add_widget(self.movie_meta)

		self.movie_text = MovieSummary(text='Summary', x=1080, width=1080)
		self.fixed_layer.add_widget(self.movie_text)

		self.meta_info = MovieMetaInfo()


		self.prev_btn = LeftButton(size=(150,250), pos=(0,1200))
		self.prev_btn.bind(on_release=self.goprev)
		self.fixed_layer.add_widget(self.prev_btn)

		self.next_btn = RightButton(size=(150,250), pos=(930,1200))
		self.next_btn.bind(on_release=self.gonext)
		self.fixed_layer.add_widget(self.next_btn)


		#buying tickets
		self.buy_btn = BuyButton(size=(1080*.3,100), pos=(1080*.7,890))
		self.buy_btn.bind(on_release=self.start_buy)
		self.fixed_layer.add_widget(self.buy_btn)

		self.buy_widget = BuyingOverlay(x=1080)
		self.fixed_layer.add_widget(self.buy_widget)


		#ADD Images
		self.ad_image = Image(pos=(1080,720), size=(1080,920))
		self.fixed_layer.add_widget(self.ad_image)
		self.select_ad()

		#movie_suggestions
		self.bottom_layer = BoxLayout(size=(1080,1920*0.4), x=2000, orientation="vertical")
		self.bottom_header = Image(source='images/header-suggestions.png', size_hint=(None, None), size=(1080,100))
		self.bottom_layer.add_widget(self.bottom_header)
		self.trailer_layer = BoxLayout()
		self.bottom_layer.add_widget(self.trailer_layer)
		self.fixed_layer.add_widget(self.bottom_layer)

		self.trailer1 = None
		self.trailer2 = None
		self.trailer3 = None

	def show_related(self, *args):
		self.bottom_header.source = 'images/header-related.png'

		anim = Animation(y=-340, t='out_quad')
		anim.start(self.bottom_layer)

		self.trailer1.video.play = False
		self.trailer2.video.play = False
		self.trailer3.video.play = False

		for c in self.trailer_layer.children[:]:
			self.trailer_layer.remove_widget(c)
		self.trailer1 = MovieThumbnail(text="trailer 1")
		self.trailer1.movie = self.app.get_random_movie()
		self.trailer_layer.add_widget(self.trailer1)

		self.trailer2 = MovieThumbnail(text="trailer 2")
		self.trailer2.movie = self.app.get_random_movie()
		self.trailer_layer.add_widget(self.trailer2)

		self.trailer3 = MovieThumbnail(text="trailer 3")
		self.trailer3.movie = self.app.get_random_movie()
		self.trailer_layer.add_widget(self.trailer3)


	def gonext(self, *args):
		global movies
		#print self.video.position
		current_key = ""
		for k, m in movies.iteritems():
			if m == self.movie:
				current_key = k
				break

		try:
			idx = self.app.suggestions.index(current_key) +1
			next_key = self.app.suggestions[idx%len(self.app.suggestions)]
			self.select_movie(movies[next_key])
		except:
			self.select_movie(movies.values()[0])
				

	def goprev(self, *args):
		global movies
		current_key = ""
		for k, m in movies.iteritems():
			if m == self.movie:
				current_key = k
				break

		try:
			idx = self.app.suggestions.index(current_key) -1
			next_key = self.app.suggestions[idx%len(self.app.suggestions)]
			self.select_movie(movies[next_key])
		except:
			self.select_movie(movies.values()[0])



	def select_movie(self, selection, *args):
		anim = Animation(y=-900, t='out_quad',d=0.7)
		anim.start(self.bottom_layer)
		anim.bind(on_complete=self.show_related)

		anim2 = Animation(x=-1080, t='out_quad',d=0.7)
		anim2.start(self.ad_image)

		anim3 = Animation(x=(1080*.7 -10), t='out_quad',d=0.7)
		anim3.start(self.buy_btn)

		anim4 = Animation(x=0, t='out_quad',d=0.7)
		anim4.start(self.prev_btn)
		anim4.start(self.video)


		animnb = Animation(x=930, t='out_quad',d=0.7)
		animnb.start(self.next_btn)

		anim5 = Animation(x=30, t='out_quad',d=0.7)
		anim5.start(self.movie_title)
		anim5.start(self.movie_meta)
		anim5.start(self.movie_text)


		self.movie = selection 
		self.movie_title.text = self.movie.title
		self.movie_title.text_size = (720,300)
		self.movie_title.padding = (20,20)
		self.movie_title.size = (700,300)
		self.movie_title.halign = 'left'


		self.movie_meta.text = "Rated: "+self.movie.rating
		self.movie_meta.text_size = (1080,100)
		self.movie_meta.size = (1080,100)
		self.movie_meta.halign = 'left'


		self.movie_text.text = self.movie.summary[:600]
		self.movie_text.text_size = (700,None)
		self.movie_text.width = 700
		self.movie_meta.halign = 'left'

		self.video.play = False
		self.video.source = ''
		self.video.source = self.movie.trailer
		self.video.play = True



	def select_ad(self, *args):
		fname = self.app.get_next_offer()
		image_buffer = self.app.ad_images[fname]
		self.ad_image._core_image = image_buffer
		self.ad_image.texture = image_buffer.texture
		Clock.schedule_once(self.select_ad, 7.0)

	def finish_buy(self, *args):
		self.app.goto(self.app.thank_you_screen)

	def start_buy(self, touch):
		self.video.play = False
		anim = Animation(x=0, t='out_elastic')
		anim.start(self.buy_widget)

	def cancel_buy(self, touch):
		self.video.play = True
		anim = Animation(x=1920, t='out_elastic')
		anim.start(self.buy_widget)

	def next_movie(self, *args):
		pass
		#self.movie_view.movie = self.app.get_random_movie()
		#self.movie_view.play()
 
	def hide(self, *args):
		self.video.play = False
		if self.trailer1:
			self.trailer1.video.play = False
			self.trailer2.video.play = False
			self.trailer3.video.play = False
		anim = Animation(x=-1500, t='out_quad', d=0.7)
		anim.start(self.bottom_layer)

		anim2 = Animation(x=-1500, t='out_quad', d=0.7)
		anim2.start(self.ad_image)

		anim3 = Animation(x=-1500, t='out_quad',d=0.7)
		anim3.start(self.video)
	
		self.buy_btn.x = 2500
		self.movie_title.x=1580
		self.next_btn.x=1580+930
		self.prev_btn.x=1580
		self.movie_text.x=1580
		self.movie_meta.x=1580
		self.buy_widget.x=1580


	def show(self, *args):
		global movies
		self.bottom_header.source = 'images/header-suggestions.png'
		self.buy_btn.x = 1920
		self.bottom_layer.pos = (1080,0)
		self.ad_image.x = 1080
		self.video.x = 1080

		anim = Animation(x=0, t='out_quad', d=1.5)
		anim.start(self.bottom_layer)
 
		anim2 = Animation(x=0, t='out_quad', d=1.5)
		anim2.start(self.ad_image)

		self.movie_title.x=1080
		self.movie_meta.x=1080
		self.movie_text.x=1080

		for c in self.trailer_layer.children[:]:
			self.trailer_layer.remove_widget(c)
		self.trailer1 = MovieThumbnail(text="trailer 1")
		self.trailer1.movie = movies[self.app.suggestions[0]]
		self.trailer_layer.add_widget(self.trailer1)

		self.trailer2 = MovieThumbnail(text="trailer 2")
		self.trailer2.movie = movies[self.app.suggestions[1]]
		self.trailer_layer.add_widget(self.trailer2)

		self.trailer3 = MovieThumbnail(text="trailer 3")
		self.trailer3.movie = movies[self.app.suggestions[2]]
		self.trailer_layer.add_widget(self.trailer3)


class ThankYouScreen(AppScreen):
	def show(self, *args):
		self.x = 1080
		anim = Animation(x=0.0, t='out_quad', d=0.7)
		anim.start(self)
		Clock.schedule_once(partial(self.app.goto, self.app.info_screen), 4.0)


from movie import Movie
import sys, json
movies = {}
	
class SockThread(threading.Thread):
	def __init__(self, address='127.0.0.1', **kwargs):
		""" TODO: remove this by adding IPC pipe """
		super(SockThread, self).__init__(**kwargs)
		self.isAlive = False
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.settimeout(2.0)
		
		self.PORT = 5489
		self.ADDRESS = address
		self.msgLock = threading.Lock()
		self.pending = False
		
	def connect(self):
		for i in range(10):
			try:
				self.socket.connect((self.ADDRESS, self.PORT))
			except socket.error as msg:
				print "SockThread Error: %s" % msg
				time.sleep(3)
				continue
			print "...Socket Connected"
			return True
		return False

	def sendObj(self, obj):
		msg = json.dumps(obj)
		if self.socket:
			frmt = "=%ds" % len(msg)
			packedMsg = struct.pack(frmt, msg)
			packedHdr = struct.pack('=I', len(packedMsg))
			
			self._send(packedHdr)
			self._send(packedMsg)
			
	def _send(self, msg):
		sent = 0
		while sent < len(msg):
			sent += self.socket.send(msg[sent:])
			
	def _read(self, size):
		data = ''
		while len(data) < size:
			dataTmp = self.socket.recv(size-len(data))
			data += dataTmp
			if dataTmp == '':
				raise RuntimeError("socket connection broken")
		return data

	def _msgLength(self):
		d = self._read(4)
		s = struct.unpack('=I', d)
		return s[0]
	
	def _readMsg(self):
		size = self._msgLength()
		data = self._read(size)
		frmt = "=%ds" % size
		msg = struct.unpack(frmt,data)
		return json.loads(msg[0])

	def stop(self):
		self.isAlive = False
		
	def isPending(self):
		return self.pending
	
	def getMsg(self):
		self.msgLock.acquire()
		self.pending = False
		tmpMsg = self.msg
		self.msgLock.release()
		return tmpMsg
		
	def run(self):
		self.isAlive = True
		while self.isAlive:
			msg = ''
			try:
				msg = self._readMsg()
			except socket.timeout as e:
				print "socket.timeout: %s" % e
				continue
			except Exception as e:
				print "%s" % e
				break
			else:
				if msg != '':
					self.msgLock.acquire()
					self.msg = msg
					self.pending = True
					self.msgLock.release()
		self.socket.close()

class MovieKiosk(App):
	'''MovieKioskApp is the application controler.
	'''
	def __init__(self, **kwargs):
		super(MovieKiosk, self).__init__(**kwargs)
		self.sockThread = SockThread()

	def on_start(self):
		if self.sockThread.connect():
			self.sockThread.sendObj({"message": "new connection"})
			self.sockThread.start()
			# TODO: remove this by adding IPC pipe
			Clock.schedule_interval(self.message_check, 0.1)
		else:
			self.sockThread.stop()
	
	def on_stop(self):
		self.sockThread.stop()

	def get_random_movie(self):
		return random.choice(movies.values())
	 
	def get_random_movies(self, n=3):
		return random.sample(movies.values(), n)

	def get_random_ad(self):
		return random.choice(self.ad_images.keys())

	def get_next_offer(self):
		old = self.offers.pop(0)
		self.offers.append(old)
		return self.offers[0]

	def goto(self, screen, animation=True):
		if screen == self.active_screen:
			return
		
		self.active_screen.hide()
		self.layout.remove_widget(screen)
		self.layout.add_widget(screen)
		screen.show()
		self.active_screen = screen

	def start(self, *args):
		self.movie_screen.hide()
		self.thank_you_screen.hide()
		self.info_screen.show()
		self.active_screen = self.info_screen

	def load_data(self):
		global movies

		self.video_data = {}
		for folder in glob('content/movies/*'):
			movie_id = folder.split('/')[-1]
			#print movie_id
			movie_data = json.loads(open(folder+'/data.json').read())
			movies[movie_id] = Movie(movie_data)
			movies[movie_id].set_trailer(folder+'/trailer.avi');
			#self.video_data[movie_id] = VideoBuffer(filename=movies[movie_id].trailer)
			
		#preload data, so it wont hang on loading
		self.ad_images = {}
		for fname in glob('content/offers/*.png'):
			self.ad_images[fname] = ImageLoader.load(fname)

		self.offers = self.ad_images.keys()
		self.suggestions = movies.keys()[:3]

	def print_fps(self, *args):
		print "FPS:", Clock.get_fps()


	def set_logo_color(self, r,g,b):
		anim = Animation(bg_r=r, bg_g=g, bg_b=b, t='out_quad')
		anim.start(self.logo)
		
	def message_check(self, td):
		""" TODO: remove this by adding IPC pipe """
		if self.sockThread.isPending():
			self.process_message(self.sockThread.getMsg())

	def process_message(self, msg):
		print "processing:", msg
		logo_color = msg.get('color', '#444444')
		r,g,b,a = get_color_from_hex(logo_color)
		self.set_logo_color(r,g,b)
		
		if msg['person_count'] == 0:
			self.movie_screen.buy_widget.num_kids = 0
			self.movie_screen.buy_widget.num_adut = 0
			return self.goto(self.info_screen)
		
		self.movie_screen.buy_widget.num_kids = msg['people']['kids']
		self.movie_screen.buy_widget.num_adults = msg['people']['adult']
		
		self.suggestions = msg['movies']
		self.offers = msg['offers']
		self.gender_mode = msg.get('gender', 'neutral')
		self.welcome_audio_file = msg['audio_message']

		self.goto(self.movie_screen)
		
	def build(self):

		self.load_data()

		root = Widget(size=(1080,1920), size_hint=(None, None))
		
		self.movie_screen = MovieScreen(app=self)
		root.add_widget(self.movie_screen)

		self.thank_you_screen = ThankYouScreen(app=self)
		root.add_widget(self.thank_you_screen)

		self.info_screen = InfoScreen(app=self)
		root.add_widget(self.info_screen)

		self.layout = root
		viewport = Viewport(size=(1080,1920))
		Clock.schedule_once(viewport.fit_to_window)
		viewport.add_widget(Image(source='images/mainbg.png', pos=(0,0), size=(1080,1920)))
		viewport.add_widget(root)
		self.logo = LogoImage(source='images/logo.png', y=1620, size=(1080,300), bgcolor=[.1,.1,.1])
		viewport.add_widget(self.logo)

		self.active_screen = self.info_screen
		Clock.schedule_once(self.start)
		Clock.schedule_interval(self.print_fps, 2.0)
		return viewport


if __name__ == '__main__':
	MovieKiosk().run()
