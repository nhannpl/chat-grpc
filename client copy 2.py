from __future__ import print_function
from curses import window
from datetime import datetime

import time

from tkinter import *
from tkinter import simpledialog

import logging 
import random
import grpc
import chat_pb2, chat_pb2_grpc
import chat_resources

import threading

from google.protobuf.timestamp_pb2 import Timestamp
SERVER_PORT="50055"



TIME_FORMAT="%Y-%m-%d %H:%M:%S"

HELP="--help"
CHAT_LIST="--chat_list"
USER_LIST="--user_list"
JOIN_CHAT="--join_chat"
CREATE_CHAT="--create_chat"
SEND_MESSAGE="--send"
LEAVE_CHAT="--leave_chat"



IN_CHAT="IN_CHAT"
HOME="HOME"




class Client:
    
    def __init__(self, u:str, window):
    
        print("Connect to server at "+SERVER_PORT)
        channel= grpc.insecure_channel("localhost:"+SERVER_PORT) #as channel:
        self.stub = chat_pb2_grpc.ChatStub(channel)
        self.username=u
        print("Connection done.")
        self.state=HOME
        
        self.lock={
        CHAT_LIST: False,
        USER_LIST:False,
        JOIN_CHAT:False,
        CREATE_CHAT:False,
        SEND_MESSAGE:False,
        LEAVE_CHAT:False
        }
        
        
        self.window=window
       # self.command=""
       # self.last_command=""
       # self.in_chat=False
        self.room_name= None
        self.setup_ui()
        self.stream=None
        self.queue=[]
        
      #  self.stub_lock=threading.Lock()
        
        self.recive_thread=threading.Thread(target=self.listen_to_server, args=[self.queue])
        self.recive_thread.start()
        
        self.new_input=False
      
        self.window.mainloop()
        
    
    def get_chat_list(self):
  
        #for room in  self.stub.ListChatRooms(chat_pb2.Empty()):
        request =chat_pb2.User(name=self.username)
        i=1
        self.console.insert(END,"\nList of chatrooms:\n")
        self.stream= self.stub.ListChatRooms(request)
        #self.console.insert(END,"\nList of chatrooms:\n")
        try:
            for m in self.stream:
                #with self.lock[CHAT_LIST]:
                    if self.lock[CHAT_LIST]:
                        self.console.insert(END, "[{}]. {} \n".format( i, m.name))
                        i+=1
                    else:
#                        self.console.insert(END,"Chat list response is terminated.")
                        self.stream.cancel()
                        self.stream = None
                        return
        except Exception as e:
            print("Error: Exception when listening to chat_list response:")
            print(e)
                
    
            
        
    def user_list_in_room(self, chat_name):
        request= chat_pb2.RequestUserRoomList(
            room_name=chat_name,
            user_name=self.username
        )
        self.console.insert(END,"\nList of users in "+chat_name+"\n")
        self.stream=self.stub.ListUserRoom(request)
        i=1
        #self.console.insert(END,"\nList of user in "+chat_name+"\n")
        try:
                for m in self.stream:
                # with self.lock[USER_LIST]:
                        if self.lock[USER_LIST]:
                            self.console.insert(END, "[{}]. {}\n".format(i,m.name))
                            i+=1
                        else:
                            #self.console.insert("User list response is terminated.")
                            self.stream.cancel()
                            self.stream = None
                            return
        except Exception as e:
            print("Error: Exception while handling user_list response:")
            print(e)
            
    def join_chat(self, chat_name):
        request = chat_pb2.JoinChatRequest(
            room_name=chat_name,
            user=chat_pb2.User(name=self.username))
        try:
        
            if self.in_chat:
                self.stream = self.stub.JoinChat(request)
                self.console.insert(END,"\n{} has just joined the chat {}.\n".format(self.username, chat_name))
                print(self.lock[JOIN_CHAT])
                
                for m in self.stream :#self.stub.JoinChat(request):
                        print("Still in joinchat")
                        print("LOCKk [joinchat]= "+str(self.lock[JOIN_CHAT]))
                # with self.lock[JOIN_CHAT]:
                        if self.lock[JOIN_CHAT]:
                            print(m.message)
                            time=m.timestamp.ToDatetime().strftime(TIME_FORMAT)
                            self.console.insert(END, "[{} @ {}]: {}\n".format(m.user.name,time, m.message))
                        else:
                            print("Joinchat listen is cancel")
                        # self.stub.JoinChat(request).cancel()
                            self.stream.cancel()
                            self.stream = None
                            #self.in_chat=False
                            self.room_name = None
                           # self.leave_chat()
                            
                            return 
                print("End of loop joinchat response")
                
            else:
                self.console.insert(END, "You need to enter a chat to be able to send a message.")
        except Exception as e:
            print("Error: Exception while handling message streaming:")
            print(e)            
        
    
    
    def get_message_to_process(self, event):
        message=self.entry_message.get() #retrieve message from ui
        if message is not '':
            #n=chat_pb2.Message(
            #    timestamp=datetime.fromtimestamp(time.time()),
             #   user=chat_pb2.User(name=self.username),
             #   message=message
           # )
            
            #self.stub.sen
            command=message.strip().split(' ')
            #self.command=command
            self.console.insert(END, "You entered: "+message+"\n")
            self.queue.append(command)
            self.run_command(command)
        
            self.entry_message.delete(0, END)
       
            
    def setup_ui(self):
        self.console=Text()
        self.console.pack(side=BOTTOM)
        self.label_username=Label(self.window, text=self.username)
        self.label_username.pack(side=LEFT)
        self.entry_message=Entry(self.window, bd=5)
        self.entry_message.bind('<Return>', self.get_message_to_process)
        self.entry_message.focus()
        self.entry_message.pack(side=TOP)            
                               
    
    def run_command(self, command):
        request_with_username=chat_pb2.User(name=self.username)
        
        if command[0]==CHAT_LIST:
            print("Get the chat list request")
            self.reset_locks()
            self.lock[CHAT_LIST]=True
            if self.stream is not None:
                self.stub.TerminateStream(request_with_username)
                
        elif command[0]==USER_LIST:
            self.reset_locks()
            self.lock[USER_LIST]=True
            #with self.stub_lock:
            if self.stream is not None:
                self.stub.TerminateStream(request_with_username)

        elif command[0]==JOIN_CHAT:
            self.reset_locks()
            self.lock[JOIN_CHAT]=True
            self.room_name=command[1]
            #with self.stub_lock:
            if self.stream is not None:
                self.stub.TerminateStream(request_with_username)


        elif command[0]==SEND_MESSAGE:
            if self.room_name is None:
                self.console.insert(END,"\nYou need to join a chat to be able to send a message.\n")
            else:          
                message= " ".join(command[1:])
                print(message)
                self.send_message(self.room_name,message)
        elif command[0]==LEAVE_CHAT:
            if self.room_name == None:
                print("You are not in any chat room.")
            else:
                if self.stream is not None:
                    self.stub.TerminateStream(request_with_username)
        elif command[0]==CREATE_CHAT:
            if self.stream is not None:
                    self.stub.TerminateStream(request_with_username)

            
                
                
            
    def listen_to_server(self, queue):
        request_with_username= chat_pb2.User(name=self.username)
        
        command =''
        last_command=''
        while True:
            if len(self.queue)>0:
                command=self.queue[0]
                if command!='':
                    #if command !=last_command:
                        if command[0]==CHAT_LIST:
                          
                            #with self.stub_lock:
                                print("Received chat list response")
                                self.stub.ResetStream(request_with_username)
                                self.get_chat_list()
                                self.console.insert(END,"Chat list response is terminated.\n")
                                self.queue.pop(0)
                        
                        elif command[0]==USER_LIST:
                            #with self.stub_lock:
                                self.stub.ResetStream(request_with_username)
                                self.user_list_in_room(command[1])
                                self.console.insert(END, "User list response is terminated.\n")
                                self.queue.pop(0)
                        
                        elif command[0]==JOIN_CHAT:
                            #with self.stub_lock:
                                self.in_chat=True
                                self.stub.ResetStream(request_with_username)
                                self.join_chat(command[1])
                                self.leave_chat() 
                                self.console.insert(END, self.username+" left the chat.\n")
                                self.queue.pop(0)
                        elif command[0]==SEND_MESSAGE:
                                self.queue.pop(0)
                                
                        elif command[0]==LEAVE_CHAT:
                            
                                self.queue.pop(0)
                                
                        elif command[0]==CREATE_CHAT:
                            room_name=" ".join(command[1:])
                            self.create_room(room_name)
                            self.queue.pop(0)
                            
                           
                       # last_command=command
                        
                        
        
    def send_message(self, room_name, message):
        request=chat_pb2.SendMessageRequest(
            user=chat_pb2.User(name=self.username),
            message=message,
            room_name=self.room_name   
        )
        response =self.stub.SendMessage(request)
          
    def leave_chat(self):
        request=chat_pb2.RequestLeaveRoom(
            room_name=self.room_name,
            user_name=self.username
        )
        self.room_name= None
        reponse=self.stub.LeaveRoom(request)
        
    def create_room(self, room_name):
        request=chat_pb2.RequestCreateNewRoom(
            room_name=room_name, 
            user=chat_pb2.User(name=self.username))
        response =self.stub.CreateRoom(request)
        self.console.insert(END,response.message )
        
     
        
        
        
          
    def show_commands_option(self):
        print("List of commands you can use:")
        print("To join an existing chatroom: --chat_list <chat_room_name>")
        print("To create a new chatroom: --user_list <chat_room_name>")    
       # elif command=="--user_list":
    

    def reset_locks(self):
            for lock_key, lock_value in self.lock.items():
                self.lock[lock_key]=False
            #print("Lock is reset. Lock[]"+JOIN_CHAT+" = "+str(self.lock[JOIN_CHAT]))
        
if __name__=="__main__":
    
    root=Tk()
    frame=Frame(root, width=500, height=500)
    frame.pack()
    root.withdraw()
    username=None
    
    while username is None:
        username=simpledialog.askstring("Username", "What's your username?")
        
    root.deiconify()
    c=Client(username, frame)

    
    
    
    