import gym
import numpy as np
from os import path
from gym_elevator.envs.conveyor import Wafer, ConveyorBelt


class ElevatorEnv(gym.Env):
	def __init__(self):
		# super(gym.Env, self).__init__()

		self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(6,), dtype=np.float)

		################################
		# action 0 : DOWN              #
		# action 1 : STAY              #
		# action 2 : UP                #
		################################
		self.action_space = gym.spaces.Discrete(3)

		self.state = None

		self.cmd_time = np.load(path.join(path.dirname(__file__), "cmd_time.npy"))
		self.departure = np.load(path.join(path.dirname(__file__), "departure.npy"))
		self.destination = np.load(path.join(path.dirname(__file__), "destination.npy"))

		self.num_data = self.cmd_time.shape[0]
		self.newly_added = None

		self.content = None

		self.elevator_pos = None
		self.is_full = None

		self.t = None
		self.dt = 0.15

		self._BEGIN = None
		self._END = None

		self.conveyors = None		# family of InConveyors

		return

	def step(self, action):

		if action == 1:
			if self.is_full:
				if self.content[1] == self.elevator_pos:
					self.content = None		# release elevator
					self.is_full = False
				else:
					pass
			else:
				if len(self.conveyors[self.elevator_pos]) == 0:
					pass
				else:
					self.content = self.conveyors[self.elevator_pos].pop(0)
					self.is_full = True

		self.elevator_pos = max(min(3, self.elevator_pos + (action - 1)), 1)

		wt = self.waiting_time

		reward = -np.sum(wt**2)
		done = False

		dest = None
		if self.content == None:
			dest = 0
		else:
			dest = self.content[1]

		self.state = np.array([float(self.is_full), dest, self.elevator_pos, wt[0], wt[1], wt[2]])

		self.simulate_arrival()		# Queue update during (t, t + dt]

		return self.state, reward, done, {}

	def reset(self):
		self._BEGIN = 0
		self._END = 0
		self.t = 0.
		self.is_full = False
		self.elevator_pos = 2		# elevator begins to operate at the 2nd floor

		self.content = None

		self.conveyors = {1: [], 2: [], 3: []}

		# self.floors = {1: ConveyorBelt(), 2: ConveyorBelt(), 3: ConveyorBelt()}
		self.state = np.array([0., 0, self.elevator_pos, 0., 0., 0.])
		return self.state

	def render(self, mode='human'):
		print('elapsed time = {:.0f} sec'.format(60. * self.t))
		print('{} wafers have arrived ({} newly added)'.format(self._BEGIN, self.newly_added))
		for i in range(3, 0, -1):
			print('Floor{} | '.format(i), end='')

			# denote the position of the elevator & whether elevator is filled
			if self.elevator_pos == i:
				print('@', end='')
				if self.is_full:
					print('o ', end='')
				else:
					print('  ', end='')
			else:
				print('   ', end='')

			print('| {:.1f}s [{:<3}]'.format(60 * (self.waiting_time[i - 1]), len(self.conveyors[i])), end='')

			print('|'.format(i), len(self.conveyors[i]) * '*')
		print('\n')
		return

	def simulate_arrival(self):
		next_t = self.t + self.dt

		while self._END < self.num_data:
			if self.t < self.cmd_time[self._END] <= next_t:
				self._END += 1
			else:
				break

		self.newly_added = self._END - self._BEGIN

		for idx in range(self._BEGIN, self._END):
			cmd_t = self.cmd_time[idx]
			depart = self.departure[idx]
			to = self.destination[idx]
			self.conveyors[depart].append((cmd_t, to))		# add load to the queue

		self.t += self.dt
		self._BEGIN = self._END

		return

	@property
	def waiting_time(self):
		wt = np.zeros(3)
		for i in range(3):

			if len(self.conveyors[i + 1]) == 0:
				wt[i] = 0.
			else:
				wt[i] = self.t - self.conveyors[i + 1][0][0]

		return wt


if __name__ == '__main__':
	"""
	arrival = np.genfromtxt('arrival.csv', delimiter=',', dtype=None)

	cmd_time = np.array([t[0] for t in arrival])
	departure = np.array([t[1] for t in arrival])
	destination = np.array([t[2] for t in arrival])

	np.save('cmd_time.npy', cmd_time)
	np.save('departure.npy', departure)
	np.save('destination.npy', destination)
	"""

	env = ElevatorEnv()

	env.reset()

	for _ in range(100):
		a = np.random.choice(4)
		_, _, _, _ = env.step(a)
		env.render()