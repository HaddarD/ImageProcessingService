import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile
from polybot.img_proc import Img


class Bot:

    def __init__(self, token, telegram_chat_url):
        self.image_path = ""
        self.images = []
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        self.telegram_bot_client.set_webhook(url=f'{telegram_chat_url}/{token}/', timeout=60)

        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

    def is_current_msg_photo(self, msg):
        return 'photo' in msg

    def download_user_photo(self, msg):
        """
        Downloads the photos that sent to the Bot to `photos` directory (should be existed)
        :return:
        """
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def handle_message(self, msg):
        """
        Determines what to do based on the message received from the user:
        Ignore files without a specific processing function.
        Reply to any text message with a qute of the message and sending user name.
        If the message has a photo in it - determines whether there's 1 or 2 images in the message and calls the menu function accordingly.
        :return:
        """
        logger.info(f'Incoming message: {msg}')
        chat_id = msg['chat']['id']
        try:
            if 'text' in msg:
                if 'entities' in msg and msg['entities'][0]['type'] == 'bot_command':
                    self.handle_filter_command(msg)
                elif msg["text"] != 'Please don\'t quote me':
                    self.send_text_with_quote(msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])
                else:
                    self.send_text(msg['chat']['id'], "Hey :D")
            elif 'document' in msg:
                pass
            elif 'photo' in msg:
                chat_id = msg['chat']['id']
                if 'media_group_id' in msg:
                    self.image_path = self.download_user_photo(msg)
                    self.images.append(self.image_path)
                    if len(self.images) == 2:
                        self.send_photo_command_menu(chat_id)
                else:
                    self.image_path = self.download_user_photo(msg)
                    self.send_photo_command_menu(chat_id)
            elif 'audi' in msg:
                pass
            elif 'voice' in msg:
                pass
            else:
                pass
        except Exception:
            self.send_text(chat_id, "Please try again")
    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        try:
            self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)
        except telebot.apihelper.ApiTelegramException as e:
            logger.error(f"Error sending text with quote: {e}")
            self.send_text(chat_id, text)  # Send the text without quote

    def send_photo_command_menu(self, chat_id):
        """
        Sends a links menu of the available filters as a response message to any image or images group received from the user
        :return:
        """
        command_menu = "Please reply with the desired filter command:\n"
        command_menu += "/blur - Apply blur filter\n"
        command_menu += "/contour - Apply contour filter\n"
        command_menu += "/rotate - Rotate the image\n"
        command_menu += "/salt_n_pepper - Apply salt and pepper noise\n"
        command_menu += "/concat - Requires 2 Images to be uploaded, & collages them together\n"
        command_menu += "/segment - Segment the image\n"
        self.send_text(chat_id, command_menu)

    def send_photo_command_submenu(self, chat_id):
        """
        Sends a links submenu of directions options when the user clicks the concat filter option
        :return:
        """
        command_submenu = "Please reply with the desired direction:\n"
        command_submenu += "/horizontal\n"
        command_submenu += "/vertical\n"
        self.send_text(chat_id, command_submenu)

    def handle_filter_command(self, msg):
        """
        Handles the user's choice of a filter by calling the corresponding function with a filter command
        :return:
        """
        chat_id = msg['chat']['id']
        command = msg['text']
        error_found = False
        processed_image_path = ""
        if command == '/concat':
            self.send_photo_command_submenu(chat_id)
        elif command == '/horizontal' or command == '/vertical':
            if self.images:
                img1 = Img(self.images[0])
                img2 = Img(self.images[1])
                result = img1.concat(img2, command)
                if result[1] == 500:
                    self.send_text(chat_id, result[0])
                    self.image_path = ""
                    self.images = []
                    return
                processed_image_path = img1.save_img()
            else:
                error_found = True
        elif self.image_path:
            img = Img(self.image_path)
            if command == '/blur':
                img.blur()
            elif command == '/contour':
                img.contour()
            elif command == '/rotate':
                img.rotate()
            elif command == '/salt_n_pepper':
                img.salt_n_pepper()
            elif command == '/segment':
                img.segment()
            else:
                # Invalid filter command
                self.send_text(chat_id, "Invalid filter command. Please choose from the command menu.")
                return
            processed_image_path = img.save_img()
        if error_found is False and processed_image_path:
            self.send_photo(chat_id, processed_image_path)
            self.image_path = ""
            self.images = []




class QuoteBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if 'text' in msg:
            if msg["text"] != 'Please don\'t quote me':
                self.send_text_with_quote(msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])
            else:
                self.send_text(msg['chat']['id'], "Hey :D")
        elif 'document' in msg:
            pass
        elif 'photo' in msg:
            pass
        elif 'audi' in msg:
            pass
        elif 'voice' in msg:
            pass
        else:
            pass


class ImageProcessingBot(Bot):
    pass
