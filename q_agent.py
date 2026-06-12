import numpy as np
import random

class QAgent:
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=1.0, epsilon_min=0.05, epsilon_decay=0.995):
        self.Q = np.zeros((3, 3))
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay

    def choose_action(self, state):
        if random.random() < self.epsilon:
            return random.randint(0, 2)
        return int(np.argmax(self.Q[state]))

    def reward(self, is_correct, old_state, new_state):
        r = (1 if is_correct else -1)
        if new_state > old_state:
            r += 1
        elif new_state < old_state:
            r -= 1
        return r

    def update(self, s, a, r, s2):
        self.Q[s, a] = self.Q[s, a] + self.alpha * (r + self.gamma * np.max(self.Q[s2]) - self.Q[s, a])
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)