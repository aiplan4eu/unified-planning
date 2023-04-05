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
   (a_lifting ?agent - distributor1_agent_type ?hoist - hoist ?crate - crate)
   (a_available ?agent - distributor1_agent_type ?hoist - hoist)
   (a_pos ?agent - distributor1_agent_type ?place - place)))
 (:action lift
  :parameters ( ?distributor1_agent - distributor1_agent_type ?p - place ?x - hoist ?y - crate ?z - surface)
  :precondition (and 
   (a_pos ?distributor1_agent ?p)
   (a_at_ ? ?x ?p)
   (a_available ?distributor1_agent ?x)
   (a_at_ ? ?y ?p)
   (a_on ? ?y ?z)
   (a_clear ? ?y)
  )
  :effect (and
   (a_lifting ?distributor1_agent ?x ?y)
   (a_clear ? ?z)
   (not (a_at_ ? ?y ?p))
   (not (a_clear ? ?y))
   (not (a_available ?distributor1_agent ?x))
   (not (a_on ? ?y ?z))
))
 (:action drop
  :parameters ( ?distributor1_agent - distributor1_agent_type ?p - place ?x - hoist ?y - crate ?z - surface)
  :precondition (and 
   (a_pos ?distributor1_agent ?p)
   (a_at_ ? ?x ?p)
   (a_at_ ? ?z ?p)
   (a_clear ? ?z)
   (a_lifting ?distributor1_agent ?x ?y)
  )
  :effect (and
   (a_available ?distributor1_agent ?x)
   (a_at_ ? ?y ?p)
   (a_clear ? ?y)
   (a_on ? ?y ?z)
   (not (a_lifting ?distributor1_agent ?x ?y))
   (not (a_clear ? ?z))
))
 (:action load
  :parameters ( ?distributor1_agent - distributor1_agent_type ?p - place ?x - hoist ?y - crate ?z_0 - truck)
  :precondition (and 
   (a_pos ?distributor1_agent ?p)
   (a_at_ ? ?x ?p)
   (a_at_ ? ?z_0 ?p)
   (a_lifting ?distributor1_agent ?x ?y)
  )
  :effect (and
   (a_in ? ?y ?z_0)
   (a_available ?distributor1_agent ?x)
   (not (a_lifting ?distributor1_agent ?x ?y))
))
 (:action unload
  :parameters ( ?distributor1_agent - distributor1_agent_type ?p - place ?x - hoist ?y - crate ?z_0 - truck)
  :precondition (and 
   (a_pos ?distributor1_agent ?p)
   (a_at_ ? ?x ?p)
   (a_at_ ? ?z_0 ?p)
   (a_available ?distributor1_agent ?x)
   (a_in ? ?y ?z_0)
  )
  :effect (and
   (a_lifting ?distributor1_agent ?x ?y)
   (not (a_in ? ?y ?z_0))
   (not (a_available ?distributor1_agent ?x))
))
)
