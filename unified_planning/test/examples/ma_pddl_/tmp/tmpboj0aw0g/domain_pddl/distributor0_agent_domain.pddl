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
   (a_lifting ?agent - distributor0_agent_type ?hoist - hoist ?crate - crate)
   (a_available ?agent - distributor0_agent_type ?hoist - hoist)
   (a_pos ?agent - distributor0_agent_type ?place - place)))
 (:action lift
  :parameters ( ?distributor0_agent - distributor0_agent_type ?p - place ?x - hoist ?y - crate ?z - surface)
  :precondition (and 
   (a_pos ?distributor0_agent ?p)
   (a------------------_at_ ?distributor0_agent ?x ?p)
   (a_available ?distributor0_agent ?x)
   (a------------------_at_ ?distributor0_agent ?y ?p)
   (a------------------_on ?distributor0_agent ?y ?z)
   (a------------------_clear ?distributor0_agent ?y)
  )
  :effect (and
   (a_lifting ?distributor0_agent ?x ?y)
   (a------------------_clear ?distributor0_agent ?z)
   (not (a------------------_at_ ?distributor0_agent ?y ?p))
   (not (a------------------_clear ?distributor0_agent ?y))
   (not (a_available ?distributor0_agent ?x))
   (not (a------------------_on ?distributor0_agent ?y ?z))
))
 (:action drop
  :parameters ( ?distributor0_agent - distributor0_agent_type ?p - place ?x - hoist ?y - crate ?z - surface)
  :precondition (and 
   (a_pos ?distributor0_agent ?p)
   (a------------------_at_ ?distributor0_agent ?x ?p)
   (a------------------_at_ ?distributor0_agent ?z ?p)
   (a------------------_clear ?distributor0_agent ?z)
   (a_lifting ?distributor0_agent ?x ?y)
  )
  :effect (and
   (a_available ?distributor0_agent ?x)
   (a------------------_at_ ?distributor0_agent ?y ?p)
   (a------------------_clear ?distributor0_agent ?y)
   (a------------------_on ?distributor0_agent ?y ?z)
   (not (a_lifting ?distributor0_agent ?x ?y))
   (not (a------------------_clear ?distributor0_agent ?z))
))
 (:action load
  :parameters ( ?distributor0_agent - distributor0_agent_type ?p - place ?x - hoist ?y - crate ?z_0 - truck)
  :precondition (and 
   (a_pos ?distributor0_agent ?p)
   (a------------------_at_ ?distributor0_agent ?x ?p)
   (a------------------_at_ ?distributor0_agent ?z_0 ?p)
   (a_lifting ?distributor0_agent ?x ?y)
  )
  :effect (and
   (a------------------_in ?distributor0_agent ?y ?z_0)
   (a_available ?distributor0_agent ?x)
   (not (a_lifting ?distributor0_agent ?x ?y))
))
 (:action unload
  :parameters ( ?distributor0_agent - distributor0_agent_type ?p - place ?x - hoist ?y - crate ?z_0 - truck)
  :precondition (and 
   (a_pos ?distributor0_agent ?p)
   (a------------------_at_ ?distributor0_agent ?x ?p)
   (a------------------_at_ ?distributor0_agent ?z_0 ?p)
   (a_available ?distributor0_agent ?x)
   (a------------------_in ?distributor0_agent ?y ?z_0)
  )
  :effect (and
   (a_lifting ?distributor0_agent ?x ?y)
   (not (a------------------_in ?distributor0_agent ?y ?z_0))
   (not (a_available ?distributor0_agent ?x))
))
)
