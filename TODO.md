* handle entity movement
  - entity-entity collisions (except on stacker)
  - MoveEntity priority (from direction): force=True, back, right, left, front
  - floor directional priority (from direction): up, left, right, down
* handle signal propagation
  - multimixers immediately pass signals through
* check which modules are allowed for each level
* maybe check module-module collisions with full hitboxes?
* set up error test cases
