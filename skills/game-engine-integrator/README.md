# game-engine-integrator

Packs and configures QC-approved assets for a specific engine target: atlas grouping by draw order and lifetime, import settings derived from recorded pivot geometry, and measured performance budgets.

Sits between `game-asset-qc` and `runtime-visual-validator` because two failure classes live there and neither neighbour can see them: an asset that is visually perfect but imports with the wrong pivot, and an asset set that is individually fine but collectively over budget.
