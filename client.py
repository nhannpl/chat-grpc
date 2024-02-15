from __future__ import print_function
from curses import window
from datetime import datetime

import time

from tkinter import *
from tkinter import simpledialog

import logging
import random
import grpc
import chat_pb2
import chat_pb2_grpc
import chat_resources

import threading

from google.protobuf.timestamp_pb2 import Timestamp
SERVER_PORT = "50055"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

HELP = "--help"
CHAT_LIST = "--chat_list"
USER_LIST = "--user_list"
JOIN_CHAT = "--join_chat"
CREATE_CHAT = "--create_chat"
SEND_MESSAGE = "--send"
LEAVE_CHAT = "--leave_chat"


class Client:

    def __init__(self, u: str, window):

        print("Connect to server at "+SERVER_PORT)
        # as channel:
        channel = grpc.insecure_channel("localhost:"+SERVER_PORT)
        self.stub = chat_pb2_grpc.ChatStub(channel)
        self.username = u
        print("Connection done.")

        self.window = window

        self.in_chat = False  # shared
        self.in_chat = threading.Lock()

        self.room_name = None  # share
        self.room_name = threading.Lock()

        self.setup_ui()
        self.stream = None  # shared
        self.stream = threading.Lock()

        self.queue = []  # shared non block, input append, output, pop(0)

      #  self.stub_lock=threading.Lock()
        self.show_commands_option()

        self.recive_thread = threading.Thread(
            target=self.listen_to_server, args=[self.queue])
        self.recive_thread.start()

        self.new_input = False

        self.window.mainloop()

    def get_chat_list(self):
        request = chat_pb2.User(name=self.username)
        i = 1
        self.console.insert(END, "\nList of chatrooms:\n")
        self.stream = self.stub.ListChatRooms(request)

        try:
            for m in self.stream:
                self.console.insert(END, "[{}]. {} \n".format(i, m.name))
                i += 1

        except Exception as e:
            print("Error: Exception when listening to chat_list response:")
            print(e)

    def user_list_in_room(self, chat_name):
        request = chat_pb2.RequestUserRoomList(
            room_name=chat_name,
            user_name=self.username
        )
        self.console.insert(END, "\nList of users in "+chat_name+"\n")
        self.stream = self.stub.ListUserRoom(request)
        i = 1
        try:
            for m in self.stream:
                if m.HasField("user"):
                    self.console.insert(
                        END, "[{}]. {}\n".format(i, m.user.name))
                    i += 1
                else:
                    self.console.insert(END, m.validation.message)
                    return

        except Exception as e:
            print("Error: Exception while handling --user_list response:")
            print(e)

    def join_chat(self, chat_name):
        request = chat_pb2.JoinChatRequest(
            room_name=chat_name,
            user=chat_pb2.User(name=self.username))
        try:

            if self.room_name != "":
                self.stream = self.stub.JoinChat(request)
                flag=False
                for m in self.stream:  # self.stub.JoinChat(request):

                    if m.HasField("message"):
                        if not self.in_chat:
                            self.console.insert(
                                END, "\n{} has just joined the chat {}.\n".format(self.username, chat_name))
                        self.in_chat = True
                        if not flag:
                            print("In chat is set to True in the message join chat")
                            flag=True
                        print("User "+self.username +
                              " just joined the chat "+self.room_name)

                        time = m.message.timestamp.ToDatetime().strftime(TIME_FORMAT)
                        self.console.insert(
                            END, "[{} @ {}]: {}\n".format(m.message.user.name, time, m.message.message))
                    elif m.HasField("validation"):
                        self.console.insert(END, m.validation.message)
                        self.in_chat = False
                        self.room_name = None
                        return
                    elif m.HasField("join_confirm"):
                       # print("There is no message in the chat. "+m.join_confirm)
                        
                        if not self.in_chat:
                            print("it' false")
                            self.console.insert(END, m.join_confirm)
                      
                        self.in_chat = True
                        if not flag:
                            flag=True
                            print("in chat is set to true in the join confirm branch")

                print("End of loop join_chat response")

            else:
                self.console.insert(
                    END, "You need to enter a chat to be able to send a message.")
        except Exception as e:
            print("Error: Exception while handling message streaming:")
            print(e)

    def get_message_to_process(self, event):
        # get('1.0', 'end-1c') #retrieve message from ui
        message = self.entry_message.get()
        if message != '':

            command = message.strip().split(' ')
            self.console.insert(END, "You entered: "+message+"\n")
            self.queue.append(command)
            self.run_command(command)
            self.entry_message.delete(0, END)

    def setup_ui(self):
        self.console = Text()
        self.console.pack(side=BOTTOM)
        scrollbar = Scrollbar(self.window, command=self.console.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.console.config(yscrollcommand=scrollbar.set)

        self.label_username = Label(self.window, text=self.username)
        self.label_username.pack(side=LEFT)
        # Text(self.window, bd=5, wrap='word', height=1.5)
        self.entry_message = Entry(self.window, bd=5)
        self.entry_message.bind('<Return>', self.get_message_to_process)
        self.entry_message.focus()
        self.entry_message.pack(side=TOP, fill='x')

    def run_command(self, command):
        request_with_username = chat_pb2.User(name=self.username)

        if command[0] == CHAT_LIST:
            print("Get the chat list request")

            if self.stream is not None:
                self.stub.TerminateStream(request_with_username)

        elif command[0] == USER_LIST:
            name = " ".join(command[1:]).strip()
            if name == "":
                self.console.insert(
                    END, "Missing room_name. Please follow the command format: "+USER_LIST+" [room name]\n")

            else:
                if self.stream is not None:
                    self.stub.TerminateStream(request_with_username)

        elif command[0] == JOIN_CHAT:
            name = " ".join(command[1:]).strip()
            if name == "":
                self.console.insert(
                    END, "Missing room_name. Please follow the command format: "+JOIN_CHAT+" [room name]\n")
            else:
                if self.stream is not None:
                    self.stub.TerminateStream(request_with_username)

        elif command[0] == SEND_MESSAGE:
            if self.in_chat == False:
                self.console.insert(
                    END, "\nYou need to join a chat to be able to send a message.\n")
            else:
                message = " ".join(command[1:])
                print(message)
                self.send_message(self.room_name, message)
        elif command[0] == LEAVE_CHAT:
            if self.room_name == None:
                self.console.insert(END, "You are not in any chat room.\n")
            else:
                if self.stream is not None:
                    self.stub.TerminateStream(request_with_username)
        elif command[0] == CREATE_CHAT:
            name = " ".join(command[1:]).strip()
            if name == "":
                self.console.insert(
                    END, "Missing room_name. Please follow the command format: "+CREATE_CHAT+" [room name]\n")
            else:

                if self.stream is not None:
                    self.stub.TerminateStream(request_with_username)

        elif command[0] == HELP:
            self.console.insert(
                END, "\n\tPlease use command follow the format below: (Brakets [] is not needed in the command)\n")
            self.show_commands_option()

        else:
            self.console.insert(
                END, "\n\n\tYour input does not match any commands. Please follow the format below: (Brakets [] is not needed in the command)\n")
            self.show_commands_option()


    def free_user(self):
        request = chat_pb2.User(name=self.username)
        
        response = self.stub.FreeUser(request)

    def listen_to_server(self, queue):
        request_with_username = chat_pb2.User(name=self.username)

        command = ''
        last_command = ''
        while True:
            if len(self.queue) > 0:
                command = self.queue[0]
                print("recive new command "+" ".join(command)+".")
                if command != '':

                    if command[0] == CHAT_LIST:

                        # with self.stub_lock:
                        print("Received chat list response")
                        self.stub.ResetStream(request_with_username)
                        self.get_chat_list()
                        self.console.insert(
                            END, "Chat list response is terminated.\n")
                        # self.queue.pop(0)

                    elif command[0] == USER_LIST:
                        # with self.stub_lock:
                        name = " ".join(command[1:]).strip()
                        if name != "":
                            print("request join "+name)

                            self.stub.ResetStream(request_with_username)
                            self.user_list_in_room(name)
                            self.console.insert(
                                END, "User list response is terminated.\n")
                            # self.queue.pop(0)

                    elif command[0] == JOIN_CHAT:
                        # with self.stub_lock:
                        name = " ".join(command[1:]).strip()
                        if name != "":

                            self.room_name = name
                            self.stub.ResetStream(request_with_username)
                            self.join_chat(name)
                            if self.in_chat:
                                self.leave_chat()

                            self.room_name = None
                    elif command[0] == SEND_MESSAGE:
                        pass

                    elif command[0] == LEAVE_CHAT:
                        pass

                    elif command[0] == CREATE_CHAT:
                        name = " ".join(command[1:]).strip()
                        if name != "":
                            self.create_room(name)

                    self.queue.pop(0)

    def send_message(self, room_name, message):
        if self.room_name is not None and self.in_chat == True:

            request = chat_pb2.SendMessageRequest(
                user=chat_pb2.User(name=self.username),
                message=message,
                room_name=self.room_name
            )
            response = self.stub.SendMessage(request)
        else:
            self.console.insert(END, "You are not in any chat room.\n")

    def leave_chat(self):
        if self.in_chat:
            request = chat_pb2.RequestLeaveRoom(
                room_name=self.room_name,
                user_name=self.username
            )

            reponse = self.stub.LeaveRoom(request)
            self.console.insert(END, self.username +
                                " left the chat "+self.room_name+".\n")
            self.room_name = None
            self.in_chat = False
            self.room_name = None

    def create_room(self, room_name):

        request = chat_pb2.RequestCreateNewRoom(
            room_name=room_name,
            user=chat_pb2.User(name=self.username))
        response = self.stub.CreateRoom(request)
        self.console.insert(END, response.message)

    def show_commands_option(self):
        self.console.insert(
            END, "\t1. To see all available chatrooms: --chat_list\n")
        self.console.insert(
            END, "\t2. To see list of users in a chatroom: --user_list [room name]\n")
        self.console.insert(
            END, "\t3. To join an existing chatroom: --join_chat [room name]\n")
        self.console.insert(
            END, "\t4. To send a message: --send [your message]\n")
        self.console.insert(
            END, "\t5. To create a new chatroom: --create_chat [room name]\n")
        self.console.insert(END, "\t6. To leave the chatroom: --leave_chat\n")
        self.console.insert(END, "\t7. Help: --help\n\n")


if __name__ == "__main__":

    root = Tk()

    frame = Frame(root, width=500, height=700)
    frame.pack()
    root.withdraw()
    username = None

    while username is None:
        username = simpledialog.askstring("Username", "What's your username?")

    root.title("Welcome: "+username)
    root.deiconify()
    c = Client(username, frame)
