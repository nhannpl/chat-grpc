import threading
import time

# Shared variable to indicate the target function
current_function = None
function_lock = threading.Lock()

# Function to be executed by the thread
def thread_function():
    global current_function
    print("Thread started.")
    while True:
        with function_lock:
            function_to_run = current_function
        if function_to_run == "func1":
            func1()
        elif function_to_run == "func2":
            func2()
        else:
            print("Unknown function specified.")
            break

# Define functions for each command
def func1():
    while True:
        print("Function 1 is running...")
        time.sleep(1)

def func2():
    while True:
        print("Function 2 is running...")
       # if current_function=="func2"
        time.sleep(1)

# Main program
def main():
    global current_function
    current_function = None
    print("Main thread started.")

    # Start the thread
    thread = threading.Thread(target=thread_function)
    thread.start()

    # User input loop
    while True:
        choice = input("Enter 'func1' or 'func2' to switch function targets, or 'quit' to exit: ")
        if choice in ["func1", "func2"]:
            with function_lock:
                current_function = choice
        elif choice == "quit":
            break
        else:
            print("Invalid command. Please try again.")

    # Wait for the thread to finish
    thread.join()
    print("Thread has finished.")

# Run the main program
if __name__ == "__main__":
    main()
