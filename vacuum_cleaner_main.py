import os.path
from tkinter import *
from tkinter import messagebox
from agents_and_environments import *
from search_algorithms import *
import sys
import math
import copy
from utilities import PriorityQueue


"""
1- BFS: Breadth first search. Using tree or graph version, whichever makes more sense for the problem
2- DFS: Depth-First search. Again using tree or graph version.
3- UCS: Uniform-Cost-Search. Using the following cost function to optimise the path, from initial to current state.
4- Greedy: Uses Manhattan distance to the next closest dirty room as heuristic for greedy algorithm. To find the next closest dirty room, use Manhattan distance.
5- A*:  Using A star search.
"""
searchTypes = ['None', 'BFS', 'DFS', 'UCS', 'Greedy', 'A*']


class VacuumPlanning(Problem):
    """ The problem of find the next room to clean in a grid of m x n rooms.
    A state is represented by state of the grid cells locations. Each room is specified by index set
    (i, j), i in range(m) and j in range (n). Final goal is to clean all dirty rooms. We go by performing sub-goals, each being cleaning the "next" dirty room.
    """

    def __init__(self, env, searchtype):
        """ Define goal state and initialise a problem
            initial is a pair (i, j) of where the agent is
            goal is next pair(k, l) where map[k][l] is dirty
        """
        self.solution = None
        self.env = env
        self.state = env.agent.location
        super().__init__(self.state)
        self.map = env.things
        self.searchType = searchtype
        env.agent.direction = 'UP'  # initial direction of the agent.
        self.agent = env.agent
        self.turnCostOn = env.turnCostOn

    def generateSolution(self):
        """ generate full path to the next goal based on type of the search chosen by user"""
        self.env.read_env()
        self.state = env.agent.location
        super().__init__(self.state)
        path = None
        explored = None
        if self.searchType == 'BFS':
            path, explored = breadth_first_graph_search(self)
        elif self.searchType == 'DFS':
            path, explored = depth_first_graph_search(self)
        elif self.searchType == 'UCS':
            path, explored = best_first_graph_search(self, lambda node: node.path_cost)
        elif self.searchType == 'Greedy':
            path, explored = best_first_graph_search(self, None)
        elif self.searchType == 'A*':
            path, explored = astar_search(self, None)
        else:
            raise 'NameError'

        if (path != None):
            self.env.set_solution(path)
        else:
            print("There is no solution!\n")
        if (explored != None):
            self.env.display_explored(explored)
        else:
            print("There is not explored list!\n")

    def generateNextSolution(self):
        self.generateSolution()

    def actions(self, state):
        """ Return the actions that can be executed in the given state.
        The result would be a list, since there are only four possible actions
        in any given state of the environment """

        possible_neighbors = self.env.things_near(state)
        possible_actions = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        for slot in possible_neighbors:
            if isinstance(slot[0], Wall):
                x, y = slot[0].location
                if x == state[0] and y == state[1] + 1:
                    possible_actions.remove('UP')
                if x == state[0] and y == state[1] - 1:
                    possible_actions.remove('DOWN')
                if x == state[0] + 1 and y == state[1]:
                    possible_actions.remove('RIGHT')
                if x == state[0] - 1 and y == state[1]:
                    possible_actions.remove('LEFT')

        return possible_actions

    def result(self, state, action):
        """ Given state and action, return a new state that is the result of the action.
        Action is assumed to be a valid action for the state """
        self.agent.direction = action
        new_state = list(state)
        if action == 'RIGHT':
            new_state[0] += 1
        elif action == 'LEFT':
            new_state[0] -= 1
        elif action == 'UP':
            new_state[1] += 1
        elif action == 'DOWN':
            new_state[1] -= 1

        return new_state

    def goal_test(self, state):
        """ Given a state, return True if state is a goal state or False, otherwise """
        return self.env.some_things_at(state, Dirt)

    def path_cost(self, curNode, state1, action, state2):
        """To be used for UCS and A* search. Returns the cost of a solution path that arrives at state2 from
        state1 via action, assuming it costs c to get up to state1. For our problem state is (x, y) coordinate pair.
        Rotation of the Vacuum machine costs equivalent of 0.5 unit for each 90' rotation. """
        move_cost = 1
        if self.turnCostOn and curNode.action != None:
            turn_cost = self.computeTurnCost(curNode.action, action)
        else:
            turn_cost = 0
        return curNode.path_cost + move_cost + turn_cost

    def computeTurnCost(self, action1, action):
        possible_actions = {"UP": 0, "DOWN": 0, "LEFT": 1, "RIGHT": 1}

        diff = abs(possible_actions[action] - possible_actions[action1])

        if diff == 0:
            if action != action1:
                return 1
            else:
                return 0
        else:
            return 0.5

    def findMinManhattanDist(self, pos):
        """find the min distance between position pos and any of the dirty rooms. Dirty rooms are maintained in
        self.env.dirtyRooms."""
        min_distance = float('inf')
        for room in self.env.dirtyRooms:
            distance = abs(pos[0] - room[0]) + abs(pos[1] - room[1])
            if distance < min_distance:
                min_distance = distance
        return min_distance

    def h(self, node):
        """ Return the heuristic value for a given state. For this problem use minimum Manhattan
        distance to a dirty room, among all the dirty rooms.
        """
        return self.findMinManhattanDist(node.state)


# ______________________________________________________________________________


def agent_label(agt):
    """creates a label based on direction"""
    dir = agt.direction
    lbl = '^'
    if dir == Direction.D:
        lbl = 'v'
    elif dir == Direction.L:
        lbl = '<'
    elif dir == Direction.R:
        lbl = '>'

    return lbl


def is_agent_label(lbl):
    """determines if the label is one of the labels tht agents have: ^ v < or >"""
    return lbl == '^' or lbl == 'v' or lbl == '<' or lbl == '>'


class Gui(VacuumEnvironment):
    """This is a two-dimensional GUI environment. Each location may be
    dirty, clean or can have a wall. The user can change these at each step.
    """
    xi, yi = (0, 0)

    # perceptible_distance = 1

    def __init__(self, root, width, height):
        self.dirtCount = 0
        self.frames = None
        self.path = None
        self.stepCount = 0
        self.searchType = None
        self.explored = None
        self.solution = None
        self.searchAgent = None
        self.turnCostOn = False
        print("creating xv with width ={} and height={}".format(width, height))
        super().__init__(width, height)

        self.agent = None
        self.root = root
        self.create_frames(height)
        self.create_buttons(width)
        self.create_walls()
        self.setupTestEnvironment()
        self.v_key_held = False  # Initialise 'V' key state
        root.bind("<KeyPress-v>", self.enable_v_key)  # Detect 'V' key press
        root.bind("<KeyRelease-v>", self.disable_v_key)  # Detect 'V' key release

        for row in self.buttons:
            for button in row:
                button.bind("<Button-1>", self.mouse_set_start_position)  # Bind mouse click



    def set_start_position(self):
        """Set the agent's starting position based on user input."""
        try:
            x = int(self.start_x_entry.get())
            y = int(self.start_y_entry.get())

            if 0 <= x < self.width and 0 <= y < self.height:
                if self.buttons[y][x]['bg'] == 'red':
                    messagebox.showinfo("Error", "Invalid start location: Cannot start on a red block.")
                    return

                # Clear the previous vacuum location
                if self.agent is not None:
                    self.buttons[self.agent.location[1]][self.agent.location[0]].config(text='', bg='white')

                # Update the agent's location
                self.agent.location = (x, y)

                # Add the vacuum symbol at the new location
                lbl = agent_label(self.agent)  # Get the correct vacuum symbol based on direction
                self.buttons[y][x].config(bg='lightgreen', text=lbl)
            else:
                messagebox.showinfo("Warning", "Invalid coordinates, must be within grid bounds.")

        except ValueError:
            messagebox.showinfo("Warning", "Please enter valid integer coordinates.")

    def create_input_fields(self):
        """Create input fields for starting position."""
        if hasattr(self, 'input_frame') and self.input_frame:
            self.input_frame.destroy()  # Remove any existing input frame

        self.input_frame = Frame(self.root, bg='black')
        self.input_frame.pack(side='top', pady=5)



    def enable_v_key(self, event):
        """Enable 'V' key detection."""
        self.v_key_held = True

    def disable_v_key(self, event):
        """Disable 'V' key detection."""
        self.v_key_held = False

    def mouse_set_start_position(self, event):
        """Set the vacuum's position based on a mouse click while holding 'V'."""
        if not getattr(self, 'v_key_held', False):  # Check if 'V' is held
            return

        # Locate the button clicked
        for row in range(len(self.buttons)):
            for col in range(len(self.buttons[row])):
                if self.buttons[row][col] == event.widget:
                    # Prevent changes if it's a red spot
                    if self.buttons[row][col]['bg'] == 'red':
                        # Do nothing and display a warning
                        messagebox.showinfo("Error", "Invalid start location: Cannot start on a red block.")
                        return

                    # Clear the previous vacuum location
                    if self.agent is not None:
                        prev_x, prev_y = self.agent.location
                        self.buttons[prev_y][prev_x].config(text='', bg='white')

                    # Update the vacuum's new location
                    self.agent.location = (col, row)
                    lbl = agent_label(self.agent)  # Get the vacuum symbol
                    self.buttons[row][col].config(bg='lightgreen', text=lbl)
                    return

    def setupTestEnvironment(self):
        """ sets up the environment"""

        xi = self.width // 2
        yi = self.height // 2
        if self.agent is None:
            theAgent = XYSearchAgent(program=XYSearchAgentProgram, loc=(yi, xi))
            xi, yi = theAgent.location
            self.add_agent(theAgent, (yi, xi))
        else:
            self.agent.location = [xi, yi]
            xi, yi = self.agent.location
            self.buttons[yi][xi].config(text='')
            self.agent.direction = 'UP'
            if len(self.agents) > 0:
                self.delete_thing(self.agents[0])
            self.add_thing(Agent(), (xi, yi))
            self.buttons[yi][xi].config(bg='white', text=agent_label(self.agent), state='normal')

        self.searchType = searchTypes[0]
        self.agent.performance = 0
        self.direction = Direction("up")

        """next create a random number of block walls inside the grid as well"""
        roomCount = (self.width - 1) * (self.height - 1)
        blockCount = random.choice(range(roomCount // 7, roomCount // 3))
        for _ in range(blockCount):
            rownum = random.choice(range(1, self.height - 1))
            colnum = random.choice(range(1, self.width - 1))
            while (rownum == yi and colnum == xi):
                rownum = random.choice(range(1, self.height - 1))
                colnum = random.choice(range(1, self.width - 1))
            self.buttons[rownum][colnum].config(bg='red', text='', disabledforeground='blue')

        self.create_dirts()
        self.stepCount = 0
        self.searchType = None
        self.solution = []
        self.explored = set()
        self.read_env()

    def create_frames(self, h):
        """Adds h row frames to the GUI environment."""
        self.frames = []
        for _ in range(h):
            frame = Frame(self.root, bg='blue')
            frame.pack(side='bottom')
            self.frames.append(frame)

    def create_buttons(self, w):
        """Adds w buttons to the respective row frames in the GUI."""
        self.buttons = []
        for frame in self.frames:
            button_row = []
            for _ in range(w):
                button = Button(frame, bg='white', state='normal', height=1, width=1, padx=1, pady=1)
                button.config(command=lambda btn=button: self.toggle_element(btn))
                button.pack(side='left')
                button_row.append(button)
            self.buttons.append(button_row)

    def create_walls(self):
        """Creates the outer boundary walls which do not move. Also create a random number of
        internal blocks of walls."""
        for row, button_row in enumerate(self.buttons):
            if row == 0 or row == len(self.buttons) - 1:
                for button in button_row:
                    button.config(bg='black', text='', state='disabled', disabledforeground='black')
            else:
                button_row[0].config(bg='black', text='', state='disabled', disabledforeground='black')
                button_row[len(button_row) - 1].config(bg='black', text='', state='disabled', disabledforeground='black')

    def create_dirts(self):
        """ set a small random number of rooms to be dirty at random location on the grid
        This function should be called after create_walls()"""
        self.read_env()  # this is needed to make sure wall objects are created
        # numRooms = (self.width-1) * (self.height -1)
        self.dirtCount = 5
        dirtCreated = 0

        self.dirtyRooms = set()

        while dirtCreated != self.dirtCount:
            rownum = random.choice(range(1, self.height - 1))
            colnum = random.choice(range(1, self.width - 1))
            if self.some_things_at((colnum, rownum)):
                continue
            self.buttons[rownum][colnum].config(bg='grey')
            dirtCreated += 1
            self.dirtyRooms.add((colnum, rownum))

    def setSearchEngine(self, choice):
        """sets the chosen search engine for solving this problem"""
        self.searchType = choice
        self.searchAgent = VacuumPlanning(self, self.searchType)
        self.searchAgent.generateSolution()
        self.done = False

    def set_solution(self, path):
        sol = path.solution()
        self.solution = list(reversed(sol))
        self.path = []
        if (self.agent == None):
            return
        while (path.state != self.agent.location):
            self.path.append(path.state)
            path = path.parent
        if (len(self.path) > 0):
            self.path.pop(0)

    def display_explored(self, explored):
        """display explored slots in a light pink color"""
        if len(self.explored) > 0:  # means we have explored list from previous search. So need to clear their visual fist
            for (x, y) in self.explored:
                self.buttons[y][x].config(bg='white')

        # now pink color the new explored list
        self.explored = explored
        for (x, y) in explored:
            self.buttons[y][x].config(bg='pink')

        # finally color orange the found path
        for (x, y) in self.path:
            self.buttons[y][x].config(bg='orange')

    def add_agent(self, agt, loc):
        """Add an agent to the GUI, ensuring only one agent exists."""
        if self.agents:  # If there are existing agents, remove them first
            for existing_agent in self.agents:
                self.delete_thing(existing_agent)

        self.add_thing(agt, loc)  # Add the new agent
        assert len(self.agents) == 1, "There should only be one agent in the environment."

        lbl = agent_label(agt)
        self.buttons[loc[1]][loc[0]].config(bg='white', text=lbl, state='normal')
        self.agent = agt

    def toggle_element(self, button):
        """toggle the element type on the GUI when a room is clicked"""
        bgcolor = button['bg']
        txt = button['text']
        if is_agent_label(txt):
            return
        else:
            if bgcolor == 'red':
                button.config(bg='grey', text='')
            elif bgcolor == 'grey':
                button.config(bg='white', text='', state='normal')
            elif bgcolor == 'white':
                button.config(bg='red', text='')

    def removeDirtyRoom(self, loc):
        for room in self.dirtyRooms:
            if (room[0] == loc[0] and room[1] == loc[1]):
                self.dirtyRooms.discard(room)
                return
        print("removeDirtyRoom: error! dirty room ({}, {}) not found".format(room[0], room[1]))

    def execute_action(self, agent, action):
        """Determines the action the agent performs."""
        if agent is None:
            return

        xi, yi = agent.location
        if action == 'Suck':
            dirt_list = self.list_things_at(agent.location, Dirt)
            if dirt_list:
                dirt = dirt_list[0]
                agent.performance += 10
                self.delete_thing(dirt)
                self.removeDirtyRoom(agent.location)
                self.buttons[yi][xi].config(bg='white', text='')
            self.buttons[yi][xi].config(bg='white')
        else:  # Move action
            agent.location = self.searchAgent.result(agent.location, action)
            self.buttons[yi][xi].config(text='', bg='white')
            xf, yf = agent.location
            self.buttons[yf][xf].config(text=agent_label(agent), bg='lightgreen')

        NumSteps_label.config(text=f"Steps: {self.stepCount}")

    def read_env(self):
        """read_env: This sets proper wall or Dirt status based on bg color"""
        """Reads the current state of the GUI environment."""
        self.dirtCount = 0
        for j, btn_row in enumerate(self.buttons):
            for i, btn in enumerate(btn_row):
                if (j != 0 and j != len(self.buttons) - 1) and (i != 0 and i != len(btn_row) - 1):
                    if self.some_things_at((i, j)):  # and (i, j) != agt_loc:
                        for thing in self.list_things_at((i, j)):
                            if not isinstance(thing, Agent):
                                self.delete_thing(thing)
                    if btn['bg'] == 'grey':  # adding dirt
                        self.add_thing(Dirt(), (i, j))
                        self.dirtCount += 1
                    elif btn['bg'] == 'red':  # adding wall
                        self.add_thing(Wall(), (i, j))

    def update_env(self):
        """Updates the GUI environment according to the current state."""
        self.read_env()
        self.step()
        self.stepCount += 1

    def step(self):
        """updates the environment one step. Currently it is associated with one click of 'Step' button.
        """
        if env.dirtCount == 0:
            print("Everything is clean. DONE!")
            self.done = True
            return

        if len(self.solution) == 0:  # agent has reached a dirty room. So the proper action is 'suck'
            self.execute_action(self.agent, 'Suck')
            self.read_env()
            if env.dirtCount > 0 and self.searchAgent is not None:
                self.searchAgent.generateNextSolution()
                self.running = False
        else:  # agent is moving towards the next goal. So the proper action is 'move'
            move = self.solution.pop()
            self.execute_action(self.agent, move)

    def run(self, delay=1):
        """Run the Environment for given number of time steps,"""
        self.running = True
        while self.done is not True:
            if self.is_done() or self.running is False:
                break
            self.update_env()
            sleep(delay)
            Tk.update(self.root)

    def reset_env(self):
        """Resets the GUI and agents environment to the initial clear state."""
        self.running = False
        NumSteps_label.config(text=str(0))

        searchTypeStr.set(searchTypes[0])

        for j, btn_row in enumerate(self.buttons):
            for i, btn in enumerate(btn_row):
                if (j != 0 and j != len(self.buttons) - 1) and (i != 0 and i != len(btn_row) - 1):
                    if self.some_things_at((i, j)):
                        for thing in self.list_things_at((i, j)):
                            self.delete_thing(thing)
                    btn.config(bg='white', text='', state='normal')

        self.setupTestEnvironment()



"""
Our search Agents ignore environment percepts for planning. The planning is done based on static
data from environment at the beginning. The environment is fully observable
"""


def XYSearchAgentProgram(percept):
    pass


class XYSearchAgent(Agent):
    """The modified SimpleRuleAgent for the GUI environment."""

    def __init__(self, program, loc):
        super().__init__(program)
        self.location = loc
        self.direction = Direction("up")
        self.searchType = searchTypes[0]
        self.stepCount = 0


if __name__ == "__main__":
    win = Tk()
    win.title("AI Vacuum Cleaner Simulator")
    win.iconbitmap("vacuum_icon.ico")

    win.geometry("500x550+50+0")
    win.resizable(True, True)

    # Input frame for grid size
    size_input_frame = Frame(win, bg='black')
    size_input_frame.pack(side='top', pady=5)

    Label(size_input_frame, text="Width:", bg='black', fg='white').pack(side='left')
    width_entry = Entry(size_input_frame, width=5)
    width_entry.pack(side='left', padx=5)
    width_entry.insert(0, "20")  # Default width

    Label(size_input_frame, text="Height:", bg='black', fg='white').pack(side='left')
    height_entry = Entry(size_input_frame, width=5)
    height_entry.pack(side='left', padx=5)
    height_entry.insert(0, "18")  # Default height


    def set_grid_size():
        """Set the grid size based on user input and dynamically resize the window."""
        try:
            width = int(width_entry.get())
            height = int(height_entry.get())

            # Enforce minimum size of 4x4
            if width < 4 or height < 4:
                raise ValueError("Minimum grid size is 4x4.")

            if width > 0 and height > 0:
                global env

                # Destroy old grid frames
                if hasattr(env, 'frames') and env.frames:
                    for frame in env.frames:
                        frame.destroy()

                # Destroy old input fields
                if hasattr(env, 'input_frame') and env.input_frame:
                    env.input_frame.destroy()

                # Dynamically resize the window
                button_size = 25  # Approximate size of each grid cell in pixels
                control_height = 100  # Height for control buttons and input fields
                win.geometry(f"{max(width * button_size, 300)}x{height * button_size + control_height}")

                # Recreate the environment with the new size
                env = Gui(win, width, height)
                env.create_input_fields()

                NumSteps_label.config(text='Steps: 0')
                searchTypeStr.set(searchTypes[0])

                # Update button commands
                next_button.config(command=env.update_env)
                reset_button.config(command=env.reset_env)
                run_button.config(command=env.run)

                messagebox.showinfo("Grid Size Updated", f"Grid set to {width}x{height}")
            else:
                raise ValueError("Invalid size")
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Error: Inputs must be whole numbers and minimum 4x4.")


    set_grid_button = Button(size_input_frame, text="Set Grid Size", command=set_grid_size)
    set_grid_button.pack(side='left', padx=5)

    # Bottom frame for controls
    frame = Frame(win, bg='light grey')
    frame.pack(side='bottom')

    NumSteps_label = Label(frame, text='Steps: 0', bg='green', fg='white', bd=2, padx=2, pady=2)
    NumSteps_label.pack(side='left')

    reset_button = Button(frame, text='Reset', height=2, width=5, padx=2, pady=2)
    reset_button.pack(side='left')
    next_button = Button(frame, text='Next', height=2, width=5, padx=2, pady=2)
    next_button.pack(side='left')
    run_button = Button(frame, text='Run', height=2, width=5, padx=2, pady=2)
    run_button.pack(side='left')

    searchTypeStr = StringVar(win)
    searchTypeStr.set(searchTypes[0])
    searchTypeStr_dropdown = OptionMenu(frame, searchTypeStr, *searchTypes,
                                        command=lambda choice: env.setSearchEngine(choice))
    searchTypeStr_dropdown.pack(side='left')

    # Initialise with default grid size
    env = Gui(win, 20, 18)
    env.create_input_fields()

    next_button.config(command=env.update_env)
    reset_button.config(command=env.reset_env)
    run_button.config(command=env.run)

    win.mainloop()
