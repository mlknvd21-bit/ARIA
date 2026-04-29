class ConversationHistory:
    def __init__(self, max_messages=20):
        self.messages = []
        self.max_messages = max_messages

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        # Limit size to avoid token overflow
        if len(self.messages) > self.max_messages * 2:
            self.messages = self.messages[-self.max_messages*2:]

    def get_messages(self):
        return self.messages.copy()

    def clear(self):
        self.messages = []
