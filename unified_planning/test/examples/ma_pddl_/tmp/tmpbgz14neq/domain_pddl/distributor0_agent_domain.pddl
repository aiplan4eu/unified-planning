(define (domain depot-domain)
 (:requirements :factored-privacy :typing)
 (:types
    locatable place depot0_agent_type distributor0_agent_type distributor1_agent_type driver0_agent_type driver1_agent_type - object
    truck hoist surface - locatable
    crate pallet - surface
 )
 (:predicates
  (at_ ?locatable - locatable ?place - place)
  (on ?crate - crate ?surface - surface)
  (in ?crate - crate ?truck - truck)
  (clear ?surface - surface)
  (:private
   (lifting ?agent - distributor0_agent_type ?hoist - hoist ?crate - crate)
   (available ?agent - distributor0_agent_type ?hoist - hoist)
   (pos ?agent - distributor0_agent_type ?place - place)))
 (:action lift
  :parameters ( ?d - distributor0_agent_type ?p - place ?x - hoist ?y - crate ?z - surface)
  :precondition (and 
   (pos ?d ?p)
   (at_ ?x ?p)
   (available ?d ?x)
   (at_ ?y ?p)
   (on ?y ?z)
   (clear ?y)
  )
  :effect (and
   (lifting ?d ?x ?y)
   (clear ?z)
   (not (at_ ?y ?p))
   (not (clear ?y))
   (not (available ?d ?x))
   (not (on ?y ?z))
))
 (:action drop
  :parameters ( ?d - distributor0_agent_type ?p - place ?x - hoist ?y - crate ?z - surface)
  :precondition (and 
   (pos ?d ?p)
   (at_ ?x ?p)
   (at_ ?z ?p)
   (clear ?z)
   (lifting ?d ?x ?y)
  )
  :effect (and
   (available ?d ?x)
   (at_ ?y ?p)
   (clear ?y)
   (on ?y ?z)
   (not (lifting ?d ?x ?y))
   (not (clear ?z))
))
 (:action load
  :parameters ( ?d - distributor0_agent_type ?p - place ?x - hoist ?y - crate ?z_0 - truck)
  :precondition (and 
   (pos ?d ?p)
   (at_ ?x ?p)
   (at_ ?z_0 ?p)
   (lifting ?d ?x ?y)
  )
  :effect (and
   (in ?y ?z_0)
   (available ?d ?x)
   (not (lifting ?d ?x ?y))
))
 (:action unload
  :parameters ( ?d - distributor0_agent_type ?p - place ?x - hoist ?y - crate ?z_0 - truck)
  :precondition (and 
   (pos ?d ?p)
   (at_ ?x ?p)
   (at_ ?z_0 ?p)
   (available ?d ?x)
   (in ?y ?z_0)
  )
  :effect (and
   (lifting ?d ?x ?y)
   (not (in ?y ?z_0))
   (not (available ?d ?x))
))
)
