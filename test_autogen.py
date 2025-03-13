from autogen import AssistantAgent, UserProxyAgent, GroupChatManager, GroupChat
import random
import sys
import io
import threading
import time


def init_chat(params):
    prompt = params["prompt"]
    # agent = params["agents"]
    # model = params["models"]
    config_list1 = [
        {
            "model": "google/gemma-2-9b-it:free",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "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",
            "price": [0, 0]
        }
    ]

    config_list2 = [
        {
            "model": "qwen/qwq-32b:free",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "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",
            "price": [0, 0]
        }
    ]

    config_list3 = [
        {
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "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",
            "price": [0, 0]
        }
    ]

    config_list4 = [
        {
            "model": "deepseek/deepseek-r1-distill-llama-70b:free",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "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",
            "price": [0, 0]
        }
    ]

    llm_config1 = {"config_list": config_list1}
    llm_config2 = {"config_list": config_list2}
    llm_config3 = {"config_list": config_list3}
    llm_config4 = {"config_list": config_list4}

    init = UserProxyAgent(
        name="Init",
        system_message="Initiator. Start the conversation.",
        code_execution_config={
            "last_n_messages": 1,
            "work_dir": "groupchat_code",
            "use_docker": False,
        },
        human_input_mode="NEVER",
    )
    user_proxy = UserProxyAgent(
        name="User_proxy",
        system_message="Executor. Execute the code written by the Coder and report the result.",
        code_execution_config={
            "last_n_messages": 6,
            "work_dir": "groupchat_code",
            "use_docker": False,
        },
        human_input_mode="NEVER",
    )

    code_writer_system_message = """You are a helpful AI assistant.
Solve tasks using your coding and language skills.
In the following cases, suggest python code (in a python coding block) or shell script (in a sh coding block) for the user to execute.
1. When you need to collect info, use the code to output the info you need, for example, browse or search the web, download/read a file, print the content of a webpage or a file, get the current date/time, check the operating system. After sufficient info is printed and the task is ready to be solved based on your language skill, you can solve the task by yourself.
2. When you need to perform some task with code, use the code to perform the task and output the result. Finish the task smartly.
Solve the task step by step if you need to. If a plan is not provided, explain your plan first. Be clear which step uses code, and which step uses your language skill.
When using code, you must indicate the script type in the code block. The user cannot provide any other feedback or perform any other action beyond executing the code you suggest. The user can't modify your code. So do not suggest incomplete code which requires users to modify. Don't use a code block if it's not intended to be executed by the user.
Put "# filename: <filename>" inside every code blocks as the first line. Don't include multiple code blocks in one response. Do not ask users to copy and paste the result. Instead, use 'print' function for the output when relevant. Check the execution result returned by the user.
If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.
"""
    coder1 = AssistantAgent(
        name="Coder_1",
        system_message=code_writer_system_message,
        llm_config=llm_config1,
    )
    coder2 = AssistantAgent(
        name="Coder_2",
        system_message=code_writer_system_message,
        llm_config=llm_config2,
    )
    coder3 = AssistantAgent(
        name="Coder_3",
        system_message=code_writer_system_message,
        llm_config=llm_config3,
    )
    pm = AssistantAgent(
        name="Product_manager",
        system_message='''You are an expert product manager that is creative in coding ideas. Additionally, ensure that the code is complete, runnable, and has "# filename: <filename>" inside the code blocks as the first line.''',
        llm_config=llm_config4,
    )

    agents = [user_proxy, coder1, coder2, coder3, pm]
    coders = [agents[1], agents[2], agents[3]]

    def state_transition(last_speaker, groupchat):
        messages = groupchat.messages

        def coder(prev=None):
            random.shuffle(coders)
            return coders[0]

        if last_speaker is init:
            return coder()
        elif last_speaker is coders[0]:
            return coders[1]
        elif last_speaker is coders[1]:
            return coders[2]
        elif last_speaker is coders[2]:
            return pm
        elif last_speaker is pm:
            return user_proxy
        elif last_speaker is user_proxy:
            if messages[-1]["content"] == "exitcode: 1":
                return coder()
            else:
                return coder()

    groupchat = GroupChat(agents=agents, messages=[], max_round=11,
                          speaker_selection_method=state_transition,)
    manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config2)

    init.initiate_chat(
        manager, message=prompt
    )


def capture_output(args):
    func = init_chat
    buffer = io.StringIO()
    sys_stdout = sys.stdout
    sys.stdout = buffer

    def target():
        try:
            func(args)
        except Exception as e:
            raise e

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(360)

    if thread.is_alive():
        raise TimeoutError(f"Function execution exceeded {360} seconds.")

    sys.stdout = sys_stdout
    return buffer.getvalue()


def main():
    prompt = "from typing import List\n\n\ndef has_close_elements(numbers: List[float], threshold: float) -> bool:\n    \"\"\" Check if in given list of numbers, are any two numbers closer to each other than\n    given threshold.\n    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)\n    False\n    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)\n    True\n    \"\"\"\n"
    # init_chat(prompt)
    output = capture_output(prompt)
    print("Output:", output)


if __name__ == "__main__":
    main()
