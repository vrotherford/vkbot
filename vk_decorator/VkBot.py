import vk
import time


class Audio:
    def __init__(self,audio):
        self.url = audio['url']
        self.aid = audio['aid']
        self.owner_id = audio['owner_id']
        self.duration = audio['duration']


class Photo:
    def __init__(self,photo):
        self.pid = photo['pid']
        self.owner_id = photo['owner_id']
        self.src_big = photo.get('src_big')
        self.src_small = photo.get('src_small')
        self.height = photo.get('height')
        self.width = photo.get('width')


class Wall:
    def __init__(self, wall):
        self.id  = wall['id']
        self.text = wall['text']
        self.from_id = wall['from_id']
        self.to_id = wall['to_id']
        self.attachments = []
        self.__add_attachments(wall.get('attachments'))

    def __add_attachments(self, attachments):
        if attachments:
            for attach in attachments:
                self.attachments.append(Attachment(attach))


class Attachment:
    def __init__(self,attachment):
        self.type = attachment['type']
        self.audios = []
        self.photos = []
        self.walls = []
        self.__creat_obj(attachment)

    def __add_audios(self,audio):
        self.audios.append(audio)

    def __add_photos(self,photo):
        self.photos.append(photo)

    def __add_walls(self,wall):
        self.walls.append(wall)

    def __creat_obj(self, attachment):
        if self.type == 'audio':
            audio = Audio(attachment[self.type])
            self.__add_audios(audio)
        if self.type == 'photo':
            photo = Photo(attachment[self.type])
            self.__add_photos(photo)
        if self.type == 'wall':
            wall = Wall(attachment[self.type])
            self.__add_walls(wall)


class User:
    def __init__(self,profile):
        self.uid = int(profile['uid'])
        self.screen_name = profile['screen_name']
        self.first_name = profile['first_name']
        self.last_name = profile['last_name']
        self.online = profile['online']
        self.photo = profile.get('photo')


class Message:
    def __init__(self,message):
        self.uid = message['uid']
        self.date = message['date']
        self.mid = message['mid']
        self.read_state = message['read_state']
        self.text = message['body']
        self.attachments = []
        self.user =[]
        self.__add_attachments(message.get('attachments'))

    def __add_attachments(self,attachments):
        if attachments:
            for attach in attachments:
                self.attachments.append(Attachment(attach))

class VkBot:
    def __init__(self, token):
        self.token = token
        self.session = vk.Session(access_token=token)
        self.VKAPI = vk.API(self.session)
        self.pts = 0
        self.attach_handlers = []
        self.message_handlers =[]
        self.message = Message

    def __check_attach_handlers(self,message):
        if self.attach_handlers:
            attachments = message.attachments
            if attachments:
                for attachment in attachments:
                    attach_type = attachment.type
                    for attach_hand in self.attach_handlers:
                        if attach_hand['type'] == attach_type:
                            attach_hand['handler'](message)

    def __check_message_handlers(self,message):
        if self.message_handlers:
            for handler in self.message_handlers:
                if handler['type'] == 'text':
                    if len(message.text):
                        handler['handler'](message)
                if handler['type'] == 'attachments':
                    if message.attachments:
                        handler['handler'](message)

    def __get_new_pts(self,history):
        return history.get('new_pts')

    def __init_messages(self,history):
        messages = []
        mess = history['messages']
        profiles = history['profiles']
        for mes in mess[1:]:
            message = Message(mes)
            messages.append(message)
        for profile in profiles:
            user = User(profile)
            message.user = user
        return messages

    def message_polling(self):
        while True:
            long_poll_server=self.VKAPI.messages.getLongPollServer(need_pts=1)
            ts = long_poll_server['ts']
            if not self.pts:
                self.pts = long_poll_server['pts']
            long_poll_history =self.VKAPI.messages.getLongPollHistory(ts=ts, pts=self.pts)
            self.pts=self.__get_new_pts(long_poll_history)
            messages = self.__init_messages(long_poll_history)
            for message in messages:
                read_state = message.read_state
                if read_state == 0:
                    self.__check_attach_handlers(message)
                    self.__check_message_handlers(message)
                    self.VKAPI.messages.markAsRead(message_ids=message.mid)
            time.sleep(3)

    def __return_attach(self, message):
        att_state = message.get('attachments', False)
        return att_state

    def __attach_type(self, attach):
        attach_type = attach['type']
        return attach_type

    def __add_attach_handler(self,handler,content_type):
        self.attach_handlers.append({
            'handler': handler,
            'type': content_type
        })

    def __add_message_handler(self,handler,content_type):
        self.message_handlers.append({
            'handler': handler,
            'type': content_type
        })

    def send_message(self, uid = None, domain = None, text = 'Empty message', attachment = None,messsage = None):
        self.VKAPI.messages.send(user_id=uid, domain= domain,message= text, attachment= attachment)

    def send_same_message(self,message,domain):
        try:
            self.send_message(domain=domain,text=message.text)
        except Exception:
            self.send_message(uid=message.uid,text='Пользователю нельзя отправлять сообщения от сообществ')

    def attach_handler(self, content_type):
        def decorator(handler):
            self.__add_attach_handler(handler,content_type)
        return decorator

    def message_handler(self, content_type):
        def decorator(handler):
            self.__add_message_handler(handler,content_type)
        return decorator