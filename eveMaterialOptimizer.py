import pulp

class MaterialOptimizer:

	def __init__(obj):		
		obj.required_materials = dict()
		obj.volume_per_ore = dict()
		obj.price_per_ore = dict()
		obj.volume_per_mineral = dict()
		obj.price_per_mineral = dict()
		obj.variable_mineral_dict = dict()
		obj.variable_ore_dict = dict()
		obj.yield_per_mineral = dict()
		obj.weight_of_volume = 0
		obj.weight_of_price = 1
		obj.volume = pulp.LpVariable('volume')
		obj.price = pulp.LpVariable('price')

	def add_ore(obj, ore_name, price_to_acquire_unit, volume_of_unit):
		# Create the Integer Variable used to solve any LP problem involving this mineral.
		obj.variable_ore_dict[ore_name] = pulp.LpVariable(ore_name, lowBound=0, cat='Integer')

		# Map the Mineral Variable to its Price and Volume *per unit*
		obj.price_per_ore[obj.variable_ore_dict[ore_name]] = price_to_acquire_unit
		obj.volume_per_ore[obj.variable_ore_dict[ore_name]] = volume_of_unit

	def set_mineral_yield_of_ore(obj, ore_name, mineral_name, yield_per_unit_ore):
		# Sets the amount of Output generated per *unit* of Mineral input.
		if mineral_name not in obj.yield_per_mineral:
			obj.yield_per_mineral[mineral_name] = dict()

		obj.yield_per_mineral[mineral_name][obj.variable_ore_dict[ore_name]] = yield_per_unit_ore

	def add_mineral(obj, mineral_name, price_to_acquire_unit, volume_of_unit):
		name = 'Purchased{}'.format(mineral_name)
		obj.variable_mineral_dict[name] = pulp.LpVariable(name, lowBound=0, cat='Integer')

		# Map the Mineral Variable to its Price and Volume *per unit*
		obj.price_per_mineral[obj.variable_mineral_dict[name]] = price_to_acquire_unit
		obj.volume_per_mineral[obj.variable_mineral_dict[name]] = volume_of_unit

	def set_required_mineral(obj, name, required_amount):
		# Sets a desired amount of output material
		obj.required_materials[name] = required_amount

	def configure_cost_function(obj, weight_of_price, weight_of_volume):
		# Sets a weight factor for each component of price and volume of the mineral.
		# Note, that if the price is in order of magnitude 10^6 and volume in 10^0 then you
		# might need to scale the weights appropriately to make them comparable!
		obj.weight_of_volume = weight_of_volume
		obj.weight_of_price = weight_of_price

	def solve_problem(obj, tolerance = 0.01, threads = 1, timeLimit = 120):
		material_model = pulp.LpProblem("MaterialProductionModel", pulp.LpMinimize)

		# Create Equality Constraints that produce the Price and Volume as independent variables.
		price_coefficients = [(mineral, obj.price_per_ore[mineral]) for mineral in obj.variable_ore_dict.values() ]
		price_coefficients.append((obj.price, -1))
		price_constraint = pulp.LpConstraint(pulp.LpAffineExpression(price_coefficients), sense = pulp.LpConstraintEQ, name = 'PriceConstraint', rhs = 0)

		volume_coefficients = [(mineral, obj.volume_per_ore[mineral]) for mineral in obj.variable_ore_dict.values() ]
		volume_coefficients.append((obj.volume, -1))
		volume_constraint = pulp.LpConstraint(pulp.LpAffineExpression(volume_coefficients), sense = pulp.LpConstraintEQ, name = 'VolumeConstraint', rhs = 0)
		
		material_model += price_constraint
		material_model += volume_constraint

		# Create Cost Function in terms of variables
		# I'll be lazy for now and just minimize price in ISK.
		material_model += (obj.weight_of_price * obj.price + obj.weight_of_volume * obj.volume)

		# Now go through the required materials and impose constraints that ensure we produce the right amount of stuff
		for material, amount in obj.required_materials.items():

			production_expr = pulp.LpAffineExpression(obj.yield_per_mineral[material].items())
			production_constraint = pulp.LpConstraint(production_expr, sense=pulp.LpConstraintGE, name='Produce{}'.format(material), rhs=amount)

			# Add Constraint to Model
			material_model += production_constraint

		solver = pulp.PULP_CBC_CMD(timeLimit = timeLimit, gapRel = tolerance, threads = threads)

		print(material_model)

		material_model.solve(solver)

		# The status of the solution is printed to the screen
		print("Status:", pulp.LpStatus[material_model.status])

		result = dict()
		for v in material_model.variables():
			result[v.name] = v.varValue
		return result


def main():
	optimizer = MaterialOptimizer()
	optimizer.set_required_mineral('Megacyte', 6575)
	optimizer.set_required_mineral('Zydrine', 21186)
	optimizer.set_required_mineral('Nocxium', 45699)
	optimizer.set_required_mineral('Isogen', 186361)
	optimizer.set_required_mineral('Mexallon', 733304)
	optimizer.set_required_mineral('Pyerite', 2930004)
	optimizer.set_required_mineral('Tritanium', 11716296)

	set_compressed_mineral_costs_and_yields(optimizer)

	optimizer.configure_cost_function(1, 0)

	# Retrieve a Solution that is within 0.1% of the Optimal Cost using 8 Threads.
	# Time Limit is the Default of 2 minutes.
	print(optimizer.solve_problem(tolerance = 1e-6, threads = 8))


def set_compressed_mineral_costs_and_yields(optimizer):
	# Arkonor (Compressed Ore)
	optimizer.add_ore('Arkonor', 522100, 8.80)
	optimizer.set_mineral_yield_of_ore('Arkonor', 'Tritanium', 100 * 13.75 * 16)
	optimizer.set_mineral_yield_of_ore('Arkonor', 'Mexallon', 100 * 1.563 * 16)
	optimizer.set_mineral_yield_of_ore('Arkonor', 'Megacyte', 100 * 0.2 * 16)

	# Bistot (Compressed Ore)
	optimizer.add_ore('Bistot', 570100, 4.40)
	optimizer.set_mineral_yield_of_ore('Bistot', 'Pyerite', 100 * 7.5 * 16)
	optimizer.set_mineral_yield_of_ore('Bistot', 'Zydrine', 100 * 0.281 * 16)
	optimizer.set_mineral_yield_of_ore('Bistot', 'Megacyte', 100 * 0.063 * 16)

	# Crokite (Compressed Ore)
	optimizer.add_ore('Crokite', 803500, 7.81)
	optimizer.set_mineral_yield_of_ore('Crokite', 'Tritanium', 100 * 13.125 * 16)
	optimizer.set_mineral_yield_of_ore('Crokite', 'Nocxium', 100 * 0.475 * 16)
	optimizer.set_mineral_yield_of_ore('Crokite', 'Zydrine', 100 * 0.084 * 16)

	# Dark_Ochre (Compressed Ore)
	optimizer.add_ore('DarkOchre', 397900, 4.20)
	optimizer.set_mineral_yield_of_ore('DarkOchre', 'Tritanium', 100 * 12.5 * 8)
	optimizer.set_mineral_yield_of_ore('DarkOchre', 'Isogen', 100 * 2.000 * 8)
	optimizer.set_mineral_yield_of_ore('DarkOchre', 'Nocxium', 100 * 0.150 * 8)

	# Gneiss (Compressed Ore)
	optimizer.add_ore('Gneiss', 285200, 1.80)
	optimizer.set_mineral_yield_of_ore('Gneiss', 'Pyerite', 100 * 4.400 * 5)
	optimizer.set_mineral_yield_of_ore('Gneiss', 'Mexallon', 100 * 4.800 * 5)
	optimizer.set_mineral_yield_of_ore('Gneiss', 'Isogen', 100 * 0.6 * 5)

	# Hedbergite (Compressed Ore)
	optimizer.add_ore('Hedbergite', 109700, 0.47)
	optimizer.set_mineral_yield_of_ore('Hedbergite', 'Pyerite', 100 * 3.333 * 3)
	optimizer.set_mineral_yield_of_ore('Hedbergite', 'Isogen', 100 * 0.667 * 3)
	optimizer.set_mineral_yield_of_ore('Hedbergite', 'Nocxium', 100 * 0.333 * 3)
	optimizer.set_mineral_yield_of_ore('Hedbergite', 'Zydrine', 100 * 0.063 * 3)

	# Hemorphite (Compressed Ore)
	optimizer.add_ore('Hemorphite', 99900, 0.86)
	optimizer.set_mineral_yield_of_ore('Hemorphite', 'Tritanium', 100 * 7.333 * 3)
	optimizer.set_mineral_yield_of_ore('Hemorphite', 'Isogen', 100 * 0.333 * 3)
	optimizer.set_mineral_yield_of_ore('Hemorphite', 'Nocxium', 100 * 0.400 * 3)
	optimizer.set_mineral_yield_of_ore('Hemorphite', 'Zydrine', 100 * 0.05 * 3)

	# Jaspet (Compressed Ore)
	optimizer.add_ore('Jaspet', 83990, 0.15)
	optimizer.set_mineral_yield_of_ore('Jaspet', 'Mexallon', 100 * 1.750 * 2)
	optimizer.set_mineral_yield_of_ore('Jaspet', 'Nocxium', 100 * 0.375 * 2)
	optimizer.set_mineral_yield_of_ore('Jaspet', 'Zydrine', 100 * 0.040 * 2)

	# Kernite (Compressed Ore)
	optimizer.add_ore('Kernite', 24900, 0.19)
	optimizer.set_mineral_yield_of_ore('Kernite', 'Tritanium', 100 * 1.117 * 1.2)
	optimizer.set_mineral_yield_of_ore('Kernite', 'Mexallon', 100 * 2.225* 1.2)
	optimizer.set_mineral_yield_of_ore('Kernite', 'Isogen', 100 * 1.117* 1.2)

	# Mercoxit (Compressed Ore)
	optimizer.add_ore('Mercoxit', 3.28e6, 0.10)
	optimizer.set_mineral_yield_of_ore('Mercoxit', 'Morphite', 100 * 0.075*40)

	optimizer.add_ore('Omber', 9200.0, 0.30)
	optimizer.set_mineral_yield_of_ore('Omber', 'Tritanium', 100 * 13.333 * 0.6)
	optimizer.set_mineral_yield_of_ore('Omber', 'Pyerite', 100 * 1.667 * 0.6)
	optimizer.set_mineral_yield_of_ore('Omber', 'Isogen', 100 * 1.417 * 0.6)

	optimizer.add_ore('Plagioclase', 8700.0, 0.15)
	optimizer.set_mineral_yield_of_ore('Plagioclase', 'Tritanium', 100 * 3.057 * 0.35)
	optimizer.set_mineral_yield_of_ore('Plagioclase', 'Pyerite', 100 * 6.086 * 0.35)
	optimizer.set_mineral_yield_of_ore('Plagioclase', 'Mexallon', 100 * 3.057 * 0.35)

	optimizer.add_ore('Pyroxeres', 11990, 0.16)
	optimizer.set_mineral_yield_of_ore('Pyroxeres', 'Tritanium', 100 * 11.7 * 0.3)
	optimizer.set_mineral_yield_of_ore('Pyroxeres', 'Pyerite', 100 * 0.833 * 0.3)
	optimizer.set_mineral_yield_of_ore('Pyroxeres', 'Mexallon', 100 * 1.667 * 0.3)
	optimizer.set_mineral_yield_of_ore('Pyroxeres', 'Nocxium', 100 * 0.167 * 0.3)

	optimizer.add_ore('Scordite', 2989.0, 0.19)
	optimizer.set_mineral_yield_of_ore('Scordite', 'Tritanium', 100 * 23.067*0.15)
	optimizer.set_mineral_yield_of_ore('Scordite', 'Pyerite', 100 * 11.533*0.15)

	optimizer.add_ore('Spodumain', 796400, 28.0)
	optimizer.set_mineral_yield_of_ore('Spodumain', 'Tritanium', 100 * 35*16)
	optimizer.set_mineral_yield_of_ore('Spodumain', 'Pyerite', 100 * 7.531*16)
	optimizer.set_mineral_yield_of_ore('Spodumain', 'Mexallon', 100 * 1.313*16)
	optimizer.set_mineral_yield_of_ore('Spodumain', 'Isogen', 100 * 0.281*16)

	optimizer.add_ore('Veldspar', 2690.0, 0.15)
	optimizer.set_mineral_yield_of_ore('Veldspar', 'Tritanium', 100 * 41.5*0.1)

if __name__ == '__main__':
	main()