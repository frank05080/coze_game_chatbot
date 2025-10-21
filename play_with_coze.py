"""
Coze 聊天 + 小车爬山游戏 一体化脚本
"""

import os
import gymnasium as gym
import numpy as np
import bpu_infer_lib
from cozepy import (
    COZE_CN_BASE_URL,
    Coze,
    TokenAuth,
    Message,
    ChatEventType,
)

# ========= Coze 配置 =========
COZE_API_TOKEN = ''
COZE_API_BASE = COZE_CN_BASE_URL
BOT_ID = ''
USER_ID = ''

# ========= 小车爬山函数 =========
def run_mountain_car(model_path='car_dqn_output.bin'):
    print(f"\n[GAME] 使用模型路径: {model_path}")

    env = gym.make('MountainCar-v0', render_mode="human")
    s, _ = env.reset()
    step = 0
    epi_r = 0

    policy_net = bpu_infer_lib.Infer(False)
    policy_net.load_model(model_path)

    print("[GAME] 开始小车爬山...")
    while True:
        step += 1
        policy_net.read_input(s, 0)
        policy_net.forward(more=True)
        policy_net.get_output()
        action = np.argmax(policy_net.outputs[0].data.reshape(3))
        sp, r, done, truncate, _ = env.step(action.squeeze().item())
        epi_r += r
        s = sp
        if done:
            env.reset()
            break

    print(f"[GAME] 结束。奖励: {epi_r}, 步数: {step}\n")

# ========= 主逻辑 =========
def chat_with_coze():
    coze = Coze(auth=TokenAuth(token=COZE_API_TOKEN), base_url=COZE_API_BASE)
    print("🤖 Coze 聊天开始！（输入 exit 退出）")

    while True:
        user_input = input("\n你：").strip()
        if user_input.lower() == "exit":
            print("👋 再见！")
            break

        # 如果用户输入中包含 game，则直接触发游戏
        if "game" in user_input.lower():
            run_mountain_car()
            continue

        print("Coze：", end="", flush=True)
        full_response = ""

        # 与 Coze 进行流式对话
        for event in coze.chat.stream(
            bot_id=BOT_ID,
            user_id=USER_ID,
            additional_messages=[
                Message.build_user_question_text(user_input),
            ],
        ):
            if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                print(event.message.content, end="", flush=True)
                full_response += event.message.content

            if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
                print()  # 换行
                print(f"[INFO] token usage: {event.chat.usage.token_count}")

        # 如果 AI 回复中包含 game，也触发游戏
        if "game" in full_response.lower():
            print("[SYSTEM] 检测到 Coze 回复包含 'game'，开始游戏！")
            run_mountain_car()


if __name__ == "__main__":
    chat_with_coze()
