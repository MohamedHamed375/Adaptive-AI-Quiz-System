# question_templates.py

TEMPLATES = {
    "RL": {
        "Easy": [
            {
                "question": "What is the main goal of Reinforcement Learning?",
                "correct": "To learn a policy that maximizes cumulative reward",
                "wrong": [
                    "To classify labeled data",
                    "To minimize prediction error",
                    "To cluster unlabeled samples"
                ]
            }
        ],

        "Medium": [
            {
                "question": "In Q-learning, what does the Q-value represent?",
                "correct": "Expected cumulative reward for taking an action in a state",
                "wrong": [
                    "Immediate reward only",
                    "Transition probability",
                    "Discount factor"
                ]
            }
        ],

        "Hard": [
            {
                "question": "What is the effect of decreasing epsilon in epsilon-greedy strategy?",
                "correct": "It reduces exploration and increases exploitation",
                "wrong": [
                    "It increases random actions",
                    "It removes learning",
                    "It increases reward noise"
                ]
            }
        ]
    },

    "GAN": {
        "Easy": [
            {
                "question": "What are the two main components of a GAN?",
                "correct": "Generator and Discriminator",
                "wrong": [
                    "Encoder and Decoder",
                    "Actor and Critic",
                    "Policy and Value network"
                ]
            }
        ],

        "Medium": [
            {
                "question": "What is the role of the Discriminator in GANs?",
                "correct": "Distinguish between real and generated data",
                "wrong": [
                    "Generate fake samples",
                    "Optimize the generator loss",
                    "Store training data"
                ]
            }
        ],

        "Hard": [
            {
                "question": "What is a common problem when training GANs?",
                "correct": "Mode collapse",
                "wrong": [
                    "Overfitting labels",
                    "Vanishing gradients in CNNs",
                    "Bias-variance tradeoff"
                ]
            }
        ]
    },

    "GameTheory": {
        "Easy": [
            {
                "question": "What does game theory study?",
                "correct": "Strategic interactions between rational agents",
                "wrong": [
                    "Random simulations",
                    "Image classification",
                    "Neural network training"
                ]
            }
        ],

        "Medium": [
            {
                "question": "What is a Nash Equilibrium?",
                "correct": "A state where no player can benefit by changing strategy alone",
                "wrong": [
                    "Maximum total reward",
                    "Randomized strategy",
                    "Dominant strategy always"
                ]
            }
        ],

        "Hard": [
            {
                "question": "In repeated games, what encourages cooperation?",
                "correct": "Future reward consideration",
                "wrong": [
                    "One-shot decisions",
                    "Random payoffs",
                    "Lack of strategy memory"
                ]
            }
        ]
    }
}
