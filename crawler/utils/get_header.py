import random
from crawler import settingsdev as settings

# 动态header
def get_header():
    user_agent = random.choice(settings.USER_AGENTS)
    header = {
        "user-agent": user_agent
    }
    return header


if __name__ == '__main__':
    print(get_header())