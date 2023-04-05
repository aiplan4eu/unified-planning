(define (domain depot-domain)
 (:requirements :factored-privacy :typing)
 (:types
    locatable place ag - object
    depot0_agent_type distributor0_agent_type distributor1_agent_type driver0_agent_type driver1_agent_type - ag
    truck hoist surface - locatable
    crate pallet - surface
 )
 (:predicates
  (at_ ?locatable - locatable ?place - place)
  (on ?crate - crate ?surface - surface)
  (in ?crate - crate ?truck - truck)
  (clear ?surface - surface)
  (:private
   (a_lifting ?agent - depot0_agent_type ?hoist - hoist ?crate - crate)
   (a_available ?agent - depot0_agent_type ?hoist - hoist)
   (a_pos ?agent - depot0_agent_type ?place - place)))
 (:action lift
  :parameters ( ?depot0_agent - depot0_agent_type ?p - place ?x - hoist ?y - crate ?z - surface)
  :precondition (and 
   (a_pos ?depot0_agent ?p)
   (at_ ?x ?p)
   (a_available ?depot0_agent ?x)
   (at_ ?y ?p)
   (on ?y ?z)
   (clear ?y)
  )
  :effect (and
   (a_lifting ?depot0_agent ?x ?y)
   (clear ?z)
   (not (at_ ?y ?p))
   (not (clear ?y))
   (not (a_available ?depot0_agent ?x))
   (not (on ?y ?z))
))
 (:action drop
  :parameters ( ?depot0_agent - depot0_agent_type ?p - place ?x - hoist ?y - crate ?z - surface)
  :precondition (and 
   (a_pos ?depot0_agent ?p)
   (at_ ?x ?p)
   (at_ ?z ?p)
   (clear ?z)
   (a_lifting ?depot0_agent ?x ?y)
  )
  :effect (and
   (a_available ?depot0_agent ?x)
   (at_ ?y ?p)
   (clear ?y)
   (on ?y ?z)
   (not (a_lifting ?depot0_agent ?x ?y))
   (not (clear ?z))
))
 (:action load
  :parameters ( ?depot0_agent - depot0_agent_type ?p - place ?x - hoist ?y - crate ?z_0 - truck)
  :precondition (and 
   (a_pos ?depot0_agent ?p)
   (at_ ?x ?p)
   (at_ ?z_0 ?p)
   (a_lifting ?depot0_agent ?x ?y)
  )
  :effect (and
   (in ?y ?z_0)
   (a_available ?depot0_agent ?x)
   (not (a_lifting ?depot0_agent ?x ?y))
))
 (:action unload
  :parameters ( ?depot0_agent - depot0_agent_type ?p - place ?x - hoist ?y - crate ?z_0 - truck)
  :precondition (and 
   (a_pos ?depot0_agent ?p)
   (at_ ?x ?p)
   (at_ ?z_0 ?p)
   (a_available ?depot0_agent ?x)
   (in ?y ?z_0)
  )
  :effect (and
   (a_lifting ?depot0_agent ?x ?y)
   (not (in ?y ?z_0))
   (not (a_available ?depot0_agent ?x))
))
)
