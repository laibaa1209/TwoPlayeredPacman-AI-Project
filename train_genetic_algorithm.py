import random
from search_agents import GeneticGhostAI, calculate_fitness

# Maze dimensions and layout (replace with your actual maze)
ROWS, COLS = 21, 21
maze = [[0 for _ in range(COLS)] for _ in range(ROWS)]  # Example maze

# Ghost and Pac-Man positions
ghost_pos = (10, 10)  # Replace with actual ghost position
pacman_pos = (5, 5)   # Replace with actual Pac-Man position

# Initialize GA
genetic_ai = GeneticGhostAI(population_size=50, gene_length=20)

# Train the GA
for generation in range(100):  # Number of generations
    def evaluate_fn(genes):
        return calculate_fitness(genes, ghost_pos, pacman_pos, maze)

    genetic_ai.evaluate(evaluate_fn)
    genetic_ai.evolve(mutation_rate=0.1)

    print(f"Generation {generation + 1}: Best Fitness = {genetic_ai.best.fitness}")

# Save the best path
best_path = []
current_pos = ghost_pos
for direction in genetic_ai.best.genes:
    if direction == 'up' and current_pos[1] > 0 and maze[current_pos[1] - 1][current_pos[0]] == 0:
        current_pos = (current_pos[0], current_pos[1] - 1)
    elif direction == 'down' and current_pos[1] < len(maze) - 1 and maze[current_pos[1] + 1][current_pos[0]] == 0:
        current_pos = (current_pos[0], current_pos[1] + 1)
    elif direction == 'left' and current_pos[0] > 0 and maze[current_pos[1]][current_pos[0] - 1] == 0:
        current_pos = (current_pos[0] - 1, current_pos[1])
    elif direction == 'right' and current_pos[0] < len(maze[0]) - 1 and maze[current_pos[1]][current_pos[0] + 1] == 0:
        current_pos = (current_pos[0] + 1, current_pos[1])
    best_path.append(current_pos)

# Save the trained path to a file
with open("trained_clyde_path.txt", "w") as f:
    f.write(str(best_path))

def train_ghost_ai(ghost_id, maze, generations=100, population_size=50):
    """Train ghost AI using genetic algorithm with enhanced parameters"""
    # Initialize genetic algorithm with larger population and more generations
    genetic_ai = GeneticGhostAI(population_size=population_size, gene_length=20)
    
    # Training parameters
    mutation_rate = 0.2  # Increased mutation rate for more exploration
    crossover_rate = 0.8  # High crossover rate for better solution sharing
    
    # Track best fitness for early stopping
    best_fitness_history = []
    no_improvement_count = 0
    
    print(f"Training Ghost {ghost_id} AI...")
    
    for generation in range(generations):
        # Evaluate population
        for individual in genetic_ai.population:
            # Simulate ghost movement
            x, y = 10, 10  # Starting position
            pacman_pos = (15, 15)  # Example Pacman position
            fitness = calculate_fitness(individual.genes, (x, y), pacman_pos, maze)
            individual.fitness = fitness
        
        # Sort population by fitness
        genetic_ai.population.sort(key=lambda x: x.fitness, reverse=True)
        
        # Track best fitness
        best_fitness = genetic_ai.population[0].fitness
        best_fitness_history.append(best_fitness)
        
        # Early stopping check
        if len(best_fitness_history) > 10:
            if best_fitness <= max(best_fitness_history[:-10]):
                no_improvement_count += 1
            else:
                no_improvement_count = 0
                
            if no_improvement_count >= 20:  # Stop if no improvement for 20 generations
                print(f"Early stopping at generation {generation}")
                break
        
        # Create new population
        new_population = []
        
        # Elitism: Keep best individuals
        elite_count = int(population_size * 0.1)  # Keep top 10%
        new_population.extend(genetic_ai.population[:elite_count])
        
        # Generate rest of population
        while len(new_population) < population_size:
            # Tournament selection
            parent1 = tournament_selection(genetic_ai.population, tournament_size=5)
            parent2 = tournament_selection(genetic_ai.population, tournament_size=5)
            
            # Crossover
            if random.random() < crossover_rate:
                child1, child2 = crossover(parent1, parent2)
            else:
                child1, child2 = parent1, parent2
            
            # Mutation with adaptive rate
            if random.random() < mutation_rate:
                mutate(child1)
            if random.random() < mutation_rate:
                mutate(child2)
            
            new_population.extend([child1, child2])
        
        genetic_ai.population = new_population[:population_size]
        
        # Print progress
        if (generation + 1) % 10 == 0:
            print(f"Generation {generation + 1}, Best Fitness: {best_fitness:.2f}")
    
    # Save best individual
    best_individual = max(genetic_ai.population, key=lambda x: x.fitness)
    with open(f"trained_ghost_{ghost_id}_path.txt", "w") as f:
        f.write(str(best_individual.genes))
    
    print(f"Training completed for Ghost {ghost_id}")
    print(f"Best fitness achieved: {best_individual.fitness:.2f}")
    
    return genetic_ai

def tournament_selection(population, tournament_size=3):
    """Tournament selection with variable tournament size"""
    tournament = random.sample(population, tournament_size)
    return max(tournament, key=lambda x: x.fitness)

def crossover(parent1, parent2):
    """Enhanced crossover with multiple crossover points"""
    if len(parent1.genes) != len(parent2.genes):
        return parent1, parent2
    
    # Create two children
    child1 = Individual(len(parent1.genes))
    child2 = Individual(len(parent2.genes))
    
    # Use multiple crossover points
    num_points = random.randint(1, 3)  # Random number of crossover points
    points = sorted(random.sample(range(len(parent1.genes)), num_points))
    
    # Perform crossover
    for i in range(len(parent1.genes)):
        if i in points:
            parent1, parent2 = parent2, parent1  # Switch parents at crossover points
        child1.genes[i] = parent1.genes[i]
        child2.genes[i] = parent2.genes[i]
    
    return child1, child2

def mutate(individual):
    """Enhanced mutation with multiple mutation types"""
    mutation_type = random.random()
    
    if mutation_type < 0.3:  # Point mutation
        # Mutate a single gene
        idx = random.randrange(len(individual.genes))
        individual.genes[idx] = random.choice(DIRECTIONS)
    
    elif mutation_type < 0.6:  # Swap mutation
        # Swap two random genes
        idx1, idx2 = random.sample(range(len(individual.genes)), 2)
        individual.genes[idx1], individual.genes[idx2] = individual.genes[idx2], individual.genes[idx1]
    
    else:  # Inversion mutation
        # Invert a random subsequence
        start = random.randrange(len(individual.genes))
        length = random.randrange(1, min(5, len(individual.genes) - start + 1))
        individual.genes[start:start+length] = reversed(individual.genes[start:start+length])