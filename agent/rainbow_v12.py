import tensorflow as tf
from anyrl.algos import DQN
from anyrl.envs import BatchedGymEnv
from anyrl.envs.wrappers import BatchedFrameStack
from anyrl.models import rainbow_models
from anyrl.rollouts import BatchedPlayer, PrioritizedReplayBuffer, NStepPlayer
from anyrl.spaces import gym_space_vectorizer
import gym_remote.exceptions as gre
from sonic_util import AllowBacktracking, make_env
def main():
    env = AllowBacktracking(make_env(stack=False, scale_rew=False))
    env = BatchedFrameStack(BatchedGymEnv([[env]]), num_images=4, concat=False)
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    with tf.Session(config=config) as sess:
        dqn = DQN(*rainbow_models(sess,
                                  env.action_space.n,
                                  gym_space_vectorizer(env.observation_space),
                                  min_val=-421,
                                  max_val=421))
        player = NStepPlayer(BatchedPlayer(env, dqn.online_net), 3)
        optimize = dqn.optimize(learning_rate=1e-4)
        sess.run(tf.global_variables_initializer())
        dqn.train(num_steps=2000000,
                  player=player,
                  replay_buffer=PrioritizedReplayBuffer(500000, 0.5, 0.4, epsilon=0.1),
                  optimize_op=optimize,
                  train_interval=1,
                  target_interval=64,
                  batch_size=32,
                  min_buffer_size=25000)
if __name__ == '__main__':
    try:
        main()
    except gre.GymRemoteError as exc:
        print('exception', exc)
