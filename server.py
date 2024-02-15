
from datetime import datetime
import logging
from concurrent import futures
import grpc 
import time 
import chat_resources

import chat_pb2
import chat_pb2_grpc

from google.protobuf.timestamp_pb2 import Timestamp
import time


MAX_ROOM_CAPACITY = 5 #people/ room

def get_user(user, user_db):
    if user in user_db:
        return True
    return False

class ChatServicer(chat_pb2_grpc.ChatServicer):#inheriting here from the protobuf 

    def __init__(self):
        self.chat_db=chat_resources.read_chat_database()
        
        self.user_db={}
        for chat in self.chat_db:
            users=chat.chatters
            for user in users:
                if user.name not in self.user_db.keys():
                    self.user_db[user.name]=False
      
       # self.terminate_current_stream=False
     
    
    
    def JoinChat(self, request, context):
    #   rpc JoinChat(RequestJoinChat) returns (stream Message){}
        found_room=None
        for room in self.chat_db:
            if room.name==request.room_name:
                found_room=room
                if len(room.chatters)<MAX_ROOM_CAPACITY:
                    room.chatters.append(request.user)
                    self.user_db[request.user.name]=False
                    last_index=0
                    while True and not self.user_db[request.user.name]:
                        if len(room.messages)==0:
                            no_message=""+request.user.name+" joined "+request.room_name+".\n"
                            
                            yield chat_pb2.JoinChatResponse(join_confirm=no_message)
                            print("There is no message in this room "+ room.name)
                        else:
                            while last_index<len(room.messages):
                                yield chat_pb2.JoinChatResponse(
                                    message=room.messages[last_index])
                                last_index+=1
                    print("Join chat: is forced to terminate ")
                    
                else:#the room is full
                     yield chat_pb2.JoinChatResponse(
                         validation=chat_pb2.Validation(
                             message="Room "+request.room_name+" is full.\n"))
        if found_room is  None:
             yield  chat_pb2.JoinChatResponse(
                    validation=chat_pb2.Validation(
                        message="Room "+request.room_name+" does not exist.\n"))

    
    def TerminateStream(self, request, context):
        print("stream is deactivated")
        self.user_db[request.name]=True
        return chat_pb2.Empty()
    
    def ResetStream(self, request, context):
        print("stream is activatated")
        self.user_db[request.name]=False
        return chat_pb2.Empty()
    
    def SendMessage(self, request, context):
    #   rpc SendMessage(SendMessageRequest) returns (Empty){}
        found_chat= None  
        for room in self.chat_db:
                    if room.name==request.room_name:
                        found_chat=room

        
        timestamp = Timestamp()
        timestamp.FromDatetime(datetime.fromtimestamp(time.time()))
        #print("the chat to send  is "+request.room_name)

        found_chat.messages.append(chat_pb2.Message(
                                    timestamp=timestamp, 
                                    user=request.user,
                                    message=request.message))
        print("Appended messgae "+request.message+" in chat "+request.room_name)
        
        return chat_pb2.Empty()
    def ListUserRoom(self, request, context) :
    #ListUserRoom(RequestUserRoomList) returns (stream User){}
            self.user_db[request.user_name]=False
            found_chat=None

            for room in self.chat_db:
                if room.name==request.room_name:
                    found_chat=room
            if found_chat is not None:
                    last_index=0
               # while True and not self.user_db[request.user_name]:
                    while last_index<len(found_chat.chatters):
                        user=found_chat.chatters[last_index]
                        last_index+=1
                        
                        yield chat_pb2.UserListResponse(
                            user=chat_pb2.User(name=user.name))
                    #print("User list: is forced to terminate ")
            else:
                yield chat_pb2.UserListResponse(validation=chat_pb2.Validation(message="Room "+request.room_name+" does not exist.\n"))

                
    def LeaveRoom(self, request, context):
        print("Inside leave room")
        del self.user_db[request.user_name]
        
        
        for room in self.chat_db:
            if room.name==request.room_name:
                print("Found room "+room.name)
                for user in room.chatters:
                    if request.user_name == user.name:
                        room.chatters.remove(chat_pb2.User(name=request.user_name))
                        print("Remove user "+request.user_name+"from database")
                        return chat_pb2.Empty()
        
        #This lien shouldn't ????  
        
              
        print("WARNING: Something wrong. How to leave if the user is not in the chat")
            
        
    
    def ListChatRooms(self, request:chat_pb2.User, context):
            last_index=0
            print("in list chat rooms")
        
            rooms=self.chat_db
            self.user_db[request.name]=False

        #while True and not self.user_db[request.name]:
            while len(rooms)>last_index:
                room=self.chat_db[last_index]
                last_index+=1
                yield room
       # print("Chat list: is forced to terminate ")

                
    
    def CreateRoom(self, request, context):
        self.user_db[request.user.name]=False
        for room in self.chat_db:
            if room.name==request.room_name:
                print("Room "+request.room_name+" is already existed.")
                return chat_pb2.Validation(message="Cannot create new room. Room "+room.name+" is existed.\n")
            
        chatters=[]
        messages=[]
        chatters.append(request.user)
        messages
        new_room=chat_pb2.ChatRoom()
        new_room.name=request.room_name
       
        self.chat_db.append(new_room)
        return chat_pb2.Validation(message="Room "+request.room_name+" is created.\n")
    
    
    def FreeUser(self, request, context):
        for room in self.chat_db:
            for users in room.chatters:
                for user in users:
                    if user.nam==request.name:
                        users.remove(request)
                        return chat_pb2.FreeUserResponse(validation ="User is chat-free.")
        return chat_pb2.FreeUserResponse(validation="User was not in any room. So user is still chat free.")
          
def serve():    
    server =grpc.server(futures.ThreadPoolExecutor(max_workers=MAX_THREADS))
    
    chat_pb2_grpc.add_ChatServicer_to_server(ChatServicer(), server)
    
    print("Starting server. Listening on port "+SERVER_PORT+" ...")
    
    server.add_insecure_port("[::]:"+SERVER_PORT)
    server.start()
    
    server.wait_for_termination()
    print("Server terminated?")
    
SERVER_PORT= "50055"
MAX_THREADS= 10
logging.basicConfig()
serve()