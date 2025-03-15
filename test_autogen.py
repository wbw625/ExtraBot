from autogen import AssistantAgent, UserProxyAgent, GroupChatManager, GroupChat
import random
import sys
import io
import threading
import time


def init_chat(params):
    prompt = params["prompt"]
    agent_list = params["agents"]
    model_list = params["models"]
    max_turns = params["max_turns"]

    if len(agent_list) != 7 or len(model_list) != 7:
        raise ValueError("Number of agents and models should be 6.")

    config_list_gemma = [
        {
            "model": "google/gemma-2-9b-it:free",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "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",
            "price": [0, 0]
        }
    ]

    config_list_qwen = [
        {
            "model": "qwen/qwq-32b:free",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "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",
            "price": [0, 0]
        }
    ]

    config_list_llama = [
        {
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "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",
            "price": [0, 0]
        }
    ]

    config_list_deepseek = [
        {
            "model": "deepseek/deepseek-r1-distill-llama-70b:free",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "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",
            "price": [0, 0]
        }
    ]

    config_list_mistral = [
        {
            "model": "mistralai/mistral-7b-instruct:free",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "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",
            "price": [0, 0]
        }
    ]

    llm_config_llama = {"config_list": config_list_llama}
    llm_config_qwen = {"config_list": config_list_qwen}
    llm_config_gemma = {"config_list": config_list_gemma}
    llm_config_deepseek = {"config_list": config_list_deepseek}
    llm_config_mistral = {"config_list": config_list_mistral}

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

    guardian_system_message = """
You are a guardrails agent and are tasked with ensuring that all parties adhere to the following responsible AI policies:

  - You MUST TERMINATE the conversation if it involves writing or running HARMFUL or DESTRUCTIVE code.
  - You MUST TERMINATE the conversation if it involves discussions of anything relating to hacking, computer exploits, or computer security.
  - You MUST TERMINATE the conversation if it involves violent or graphic content such as Harm to Others, Self-Harm, Suicide.
  - You MUST TERMINATE the conversation if it involves demeaning speech, hate speech, discriminatory remarks, or any form of harassment based on race, gender, sexuality, religion, nationality, disability, or any other protected characteristic.
  - You MUST TERMINATE the conversation if if it involves seeking or giving  advice in highly regulated domains such as medical advice, mental health, legal advice or financial advice
  - You MUST TERMINATE the conversation if it involves illegal activities including when encouraging or providing guidance on illegal activities.
  - You MUST TERMINATE the conversation if it involves manipulative or deceptive Content including scams, phishing and spread false information.
  - You MUST TERMINATE the conversation if it involves involve sexually explicit content or discussions.
  - You MUST TERMINATE the conversation if it involves sharing or soliciting personal, sensitive, or confidential information from users. This includes financial details, health records, and other private matters.
  - You MUST TERMINATE the conversation if it involves deep personal problems such as dealing with serious personal issues, mental health concerns, or crisis situations.

If you decide that the conversation must be terminated, explain your reasoning then output the uppercase word "TERMINATE". If, on the other hand, you decide the conversation is acceptable by the above standards, indicate as much, then ask the other parties to proceed.
"""

    pm_system_message = """
You are an expert product manager that is creative in coding ideas. Additionally, ensure that the code is complete, runnable, and has "# filename: <filename>" inside the code blocks as the first line.
"""

    # coder1 = AssistantAgent(
    #     name="Coder_1",
    #     system_message=code_writer_system_message,
    #     llm_config=llm_config_llama,
    # )
    # coder2 = AssistantAgent(
    #     name="Coder_2",
    #     system_message=code_writer_system_message,
    #     llm_config=llm_config_llama,
    # )
    # coder3 = AssistantAgent(
    #     name="Coder_3",
    #     system_message=code_writer_system_message,
    #     llm_config=llm_config_llama,
    # )
    # pm = AssistantAgent(
    #     name="Product_manager",
    #     system_message=pm_system_message,
    #     llm_config=llm_config_llama,
    # )

    # agents = [user_proxy, coder1, coder2, coder3, pm]

    agents = [user_proxy]
    cnt = 0
    coder_cnt = 0
    pm_cnt = 0
    guardian_cnt = 0

    for agent, model in zip(agent_list, model_list):
        if agent == "user_proxy":
            break
        elif agent == "coder":
            coder_cnt += 1
            cnt += 1
            agents.append(AssistantAgent(
                name=f"Coder{coder_cnt}({model})",
                system_message=code_writer_system_message,
                llm_config=locals()[f"llm_config_{model}"]
            ))
        elif agent == "product_manager":
            pm_cnt += 1
            cnt += 1
            agents.append(AssistantAgent(
                name=f"Product_manager{pm_cnt}({model})",
                system_message=pm_system_message,
                llm_config=locals()[f"llm_config_{model}"]
            ))
        elif agent == "guardian":
            guardian_cnt += 1
            cnt += 1
            agents.append(AssistantAgent(
                name=f"Guardian{guardian_cnt}({model})",
                system_message=guardian_system_message,
                llm_config=locals()[f"llm_config_{model}"]
            ))


    def state_transition(last_speaker, groupchat):
        length = len(agents)
        messages = groupchat.messages

        if last_speaker is init:
            return agents[1]
        for _ in range(length):
            if last_speaker is agents[_]:
                return agents[(_+1)%length]
        return user_proxy

    round = max_turns
    groupchat = GroupChat(agents=agents, messages=[], max_round=round*(len(agents))+1 , speaker_selection_method=state_transition)
    manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config_llama)

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
