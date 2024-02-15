from datetime import datetime
import json

from google.protobuf.timestamp_pb2 import Timestamp
import chat_pb2

def read_chat_database():
    chat_list =[]

    
    with open("chat_db.json") as chat_db_file:
        db=json.load(chat_db_file)
        print(db)
       
        for chat_room, value in db.items():
            
            chatters_raw=value["chatters"]
            chatters=[]
            for user in chatters_raw:
                chatters.append(chat_pb2.User(name=user))
                
            messages_raw=value["messages"]
            messages=[]
            for m_key, m_content in messages_raw.items():
                m_key=m_key.split('@')
                m_key[1]=m_key[1].strip()
                datetime_obj = datetime.strptime(m_key[1], "%Y-%m-%dT%H:%M:%S")
            
                timstm=Timestamp()
                timstm.FromDatetime(datetime_obj)
                messages.append(chat_pb2.Message(
                    timestamp= timstm, 
                    user=chat_pb2.User(name=m_key[0]),
                    message=m_content))
                
            group_chat= chat_pb2.ChatRoom(
                name=chat_room,
                messages=messages,
                chatters=chatters
            )
            
            chat_list.append(group_chat)
            
            
    return chat_list

def read_user_database():
    user_list =[]
    
    
    return user_list
    
            