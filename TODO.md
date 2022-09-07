* decide how to pass signals around
* implement module behavior
  - need to spawn different Entity subclasses depending on level
* handle entity movement
  - entity-entity collisions (except on stacker)
  - entity-machine collisions (except where reversing is allowed)
  - entity-wall collisions ("Products cannot leave the Factory")
  - MoveEntity priority (from direction): force=True, back, right, left, front
  - floor directional priority (from direction): top, left, right, bottom
* check which modules are allowed for each level
* maybe check module-module collisions?
* set up error test cases
