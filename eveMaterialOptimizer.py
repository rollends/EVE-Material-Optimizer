import pulp

class MaterialOptimizer:

	def __init__(obj):		
		obj.required_materials = dict()
		obj.volume_per_mineral = dict()
		obj.price_per_mineral = dict()
		obj.variable_mineral_dict = dict()
		obj.yield_per_mineral = dict()
		obj.weight_of_volume = 0
		obj.weight_of_price = 1
		obj.volume = pulp.LpVariable('volume')
		obj.price = pulp.LpVariable('price')

	def add_mineral(obj, mineral, price_to_acquire_unit, volume_of_unit):
		# Create the Integer Variable used to solve any LP problem involving this mineral.
		obj.variable_mineral_dict[mineral] = pulp.LpVariable(mineral, lowBound=0, cat='Integer')

		# Map the Mineral Variable to its Price and Volume *per unit*
		obj.price_per_mineral[obj.variable_mineral_dict[mineral]] = price_to_acquire_unit
		obj.volume_per_mineral[obj.variable_mineral_dict[mineral]] = volume_of_unit

	def set_yield_of_mineral(obj, mineral_name, output_name, yield_per_unit_mineral):
		# Sets the amount of Output generated per *unit* of Mineral input.

		if output_name not in obj.yield_per_mineral:
			obj.yield_per_mineral[output_name] = dict()

		obj.yield_per_mineral[output_name][obj.variable_mineral_dict[mineral_name]] = yield_per_unit_mineral

	def set_required_material(obj, name, required_amount):
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
		price_coefficients = [(mineral, obj.price_per_mineral[mineral]) for mineral in obj.variable_mineral_dict.values() ]
		price_coefficients.append((obj.price, -1))
		price_constraint = pulp.LpConstraint(pulp.LpAffineExpression(price_coefficients), sense = pulp.LpConstraintEQ, name = 'PriceConstraint', rhs = 0)

		volume_coefficients = [(mineral, obj.volume_per_mineral[mineral]) for mineral in obj.variable_mineral_dict.values() ]
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
	optimizer.set_required_material('Megacyte', 6575)
	optimizer.set_required_material('Zydrine', 21186)
	optimizer.set_required_material('Nocxium', 45699)
	optimizer.set_required_material('Isogen', 186361)
	optimizer.set_required_material('Mexallon', 733304)
	optimizer.set_required_material('Pyerite', 2930004)
	optimizer.set_required_material('Tritanium', 11716296)

	set_compressed_mineral_costs_and_yields(optimizer)

	optimizer.configure_cost_function(0, 1)

	# Retrieve a Solution that is within 0.1% of the Optimal Cost using 8 Threads.
	# Time Limit is the Default of 2 minutes.
	print(optimizer.solve_problem(tolerance = 1e-3, threads = 8))


def set_compressed_mineral_costs_and_yields(optimizer):
	# Arkonor (Compressed Ore)
	optimizer.add_mineral('Arkonor', 522100, 8.80)
	optimizer.set_yield_of_mineral('Arkonor', 'Tritanium', 100 * 13.75)
	optimizer.set_yield_of_mineral('Arkonor', 'Mexallon', 100 * 1.563)
	optimizer.set_yield_of_mineral('Arkonor', 'Megacyte', 100 * 0.2)

	# Bistot (Compressed Ore)
	optimizer.add_mineral('Bistot', 570100, 4.40)
	optimizer.set_yield_of_mineral('Bistot', 'Pyerite', 100 * 7.5)
	optimizer.set_yield_of_mineral('Bistot', 'Zydrine', 100 * 0.281)
	optimizer.set_yield_of_mineral('Bistot', 'Megacyte', 100 * 0.063)

	# Crokite (Compressed Ore)
	optimizer.add_mineral('Crokite', 339.24, 16)
	optimizer.set_yield_of_mineral('Crokite', 'Tritanium', 100 * 13.125)
	optimizer.set_yield_of_mineral('Crokite', 'Nocxium', 100 * 0.475)
	optimizer.set_yield_of_mineral('Crokite', 'Zydrine', 100 * 0.084)

	# Dark_Ochre (Compressed Ore)
	optimizer.add_mineral('DarkOchre', 397900, 7.81)
	optimizer.set_yield_of_mineral('DarkOchre', 'Tritanium', 100 * 12.5)
	optimizer.set_yield_of_mineral('DarkOchre', 'Isogen', 100 * 2.000)
	optimizer.set_yield_of_mineral('DarkOchre', 'Nocxium', 100 * 0.150)

	# Gneiss (Compressed Ore)
	optimizer.add_mineral('Gneiss', 285200, 1.80)
	optimizer.set_yield_of_mineral('Gneiss', 'Pyerite', 100 * 4.400)
	optimizer.set_yield_of_mineral('Gneiss', 'Mexallon', 100 * 4.800)
	optimizer.set_yield_of_mineral('Gneiss', 'Isogen', 100 * 0.6)

	# Hedbergite (Compressed Ore)
	optimizer.add_mineral('Hedbergite', 109700, 0.47)
	optimizer.set_yield_of_mineral('Hedbergite', 'Pyerite', 100 * 3.333)
	optimizer.set_yield_of_mineral('Hedbergite', 'Isogen', 100 * 0.667)
	optimizer.set_yield_of_mineral('Hedbergite', 'Nocxium', 100 * 0.333)
	optimizer.set_yield_of_mineral('Hedbergite', 'Zydrine', 100 * 0.063)

	# Hemorphite (Compressed Ore)
	optimizer.add_mineral('Hemorphite', 99900, 0.86)
	optimizer.set_yield_of_mineral('Hemorphite', 'Tritanium', 100 * 7.333)
	optimizer.set_yield_of_mineral('Hemorphite', 'Isogen', 100 * 0.333)
	optimizer.set_yield_of_mineral('Hemorphite', 'Nocxium', 100 * 0.400)
	optimizer.set_yield_of_mineral('Hemorphite', 'Zydrine', 100 * 0.05)

	# Jaspet (Compressed Ore)
	optimizer.add_mineral('Jaspet', 83990, 0.15)
	optimizer.set_yield_of_mineral('Jaspet', 'Mexallon', 100 * 1.750)
	optimizer.set_yield_of_mineral('Jaspet', 'Nocxium', 100 * 0.375)
	optimizer.set_yield_of_mineral('Jaspet', 'Zydrine', 100 * 0.040)

	# Kernite (Compressed Ore)
	optimizer.add_mineral('Kernite', 24900, 0.19)
	optimizer.set_yield_of_mineral('Kernite', 'Tritanium', 100 * 1.117)
	optimizer.set_yield_of_mineral('Kernite', 'Mexallon', 100 * 2.225)
	optimizer.set_yield_of_mineral('Kernite', 'Isogen', 100 * 1.117)

	# Mercoxit (Compressed Ore)
	optimizer.add_mineral('Mercoxit', 3.28e6, 0.10)
	optimizer.set_yield_of_mineral('Mercoxit', 'Morphite', 100 * 0.075)

	optimizer.add_mineral('Omber', 9200.0, 0.30)
	optimizer.set_yield_of_mineral('Omber', 'Tritanium', 100 * 13.333)
	optimizer.set_yield_of_mineral('Omber', 'Pyerite', 100 * 1.667)
	optimizer.set_yield_of_mineral('Omber', 'Isogen', 100 * 1.417)

	optimizer.add_mineral('Plagioclase', 8700.0, 0.15)
	optimizer.set_yield_of_mineral('Plagioclase', 'Tritanium', 100 * 3.057)
	optimizer.set_yield_of_mineral('Plagioclase', 'Pyerite', 100 * 6.086)
	optimizer.set_yield_of_mineral('Plagioclase', 'Mexallon', 100 * 3.057)

	optimizer.add_mineral('Pyroxeres', 11990, 0.16)
	optimizer.set_yield_of_mineral('Pyroxeres', 'Tritanium', 100 * 11.7)
	optimizer.set_yield_of_mineral('Pyroxeres', 'Pyerite', 100 * 0.833)
	optimizer.set_yield_of_mineral('Pyroxeres', 'Mexallon', 100 * 1.667)
	optimizer.set_yield_of_mineral('Pyroxeres', 'Nocxium', 100 * 0.167)

	optimizer.add_mineral('Scordite', 2989.0, 0.19)
	optimizer.set_yield_of_mineral('Scordite', 'Tritanium', 100 * 23.067)
	optimizer.set_yield_of_mineral('Scordite', 'Pyerite', 100 * 11.533)

	optimizer.add_mineral('Spodumain', 796400, 28.0)
	optimizer.set_yield_of_mineral('Spodumain', 'Tritanium', 100 * 35)
	optimizer.set_yield_of_mineral('Spodumain', 'Pyerite', 100 * 7.531)
	optimizer.set_yield_of_mineral('Spodumain', 'Mexallon', 100 * 1.313)
	optimizer.set_yield_of_mineral('Spodumain', 'Isogen', 100 * 0.281)

	optimizer.add_mineral('Veldspar', 2690.0, 0.15)
	optimizer.set_yield_of_mineral('Veldspar', 'Tritanium', 100 * 41.5)

if __name__ == '__main__':
	main()