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
   (a_lifting ?agent - depot0_agent_type ?hoist - hoist ?crate - crate)
   (a_available ?agent - depot0_agent_type ?hoist - hoist)
   (a_pos ?agent - depot0_agent_type ?place - place)))
 (:action lift
  :parameters ( ?depot0_agent - depot0_agent_type ?p - place ?x - hoist ?y - crate ?z - surface)
  :precondition (and 
   (a_pos ?depot0_agent ?p)
   (a------------------_at_ ?depot0_agent ?x ?p)
   (a_available ?depot0_agent ?x)
   (a------------------_at_ ?depot0_agent ?y ?p)
   (a------------------_on ?depot0_agent ?y ?z)
   (a------------------_clear ?depot0_agent ?y)
  )
  :effect (and
   (a_lifting ?depot0_agent ?x ?y)
   (a------------------_clear ?depot0_agent ?z)
   (not (a------------------_at_ ?depot0_agent ?y ?p))
   (not (a------------------_clear ?depot0_agent ?y))
   (not (a_available ?depot0_agent ?x))
   (not (a------------------_on ?depot0_agent ?y ?z))
))
 (:action drop
  :parameters ( ?depot0_agent - depot0_agent_type ?p - place ?x - hoist ?y - crate ?z - surface)
  :precondition (and 
   (a_pos ?depot0_agent ?p)
   (a------------------_at_ ?depot0_agent ?x ?p)
   (a------------------_at_ ?depot0_agent ?z ?p)
   (a------------------_clear ?depot0_agent ?z)
   (a_lifting ?depot0_agent ?x ?y)
  )
  :effect (and
   (a_available ?depot0_agent ?x)
   (a------------------_at_ ?depot0_agent ?y ?p)
   (a------------------_clear ?depot0_agent ?y)
   (a------------------_on ?depot0_agent ?y ?z)
   (not (a_lifting ?depot0_agent ?x ?y))
   (not (a------------------_clear ?depot0_agent ?z))
))
 (:action load
  :parameters ( ?depot0_agent - depot0_agent_type ?p - place ?x - hoist ?y - crate ?z_0 - truck)
  :precondition (and 
   (a_pos ?depot0_agent ?p)
   (a------------------_at_ ?depot0_agent ?x ?p)
   (a------------------_at_ ?depot0_agent ?z_0 ?p)
   (a_lifting ?depot0_agent ?x ?y)
  )
  :effect (and
   (a------------------_in ?depot0_agent ?y ?z_0)
   (a_available ?depot0_agent ?x)
   (not (a_lifting ?depot0_agent ?x ?y))
))
 (:action unload
  :parameters ( ?depot0_agent - depot0_agent_type ?p - place ?x - hoist ?y - crate ?z_0 - truck)
  :precondition (and 
   (a_pos ?depot0_agent ?p)
   (a------------------_at_ ?depot0_agent ?x ?p)
   (a------------------_at_ ?depot0_agent ?z_0 ?p)
   (a_available ?depot0_agent ?x)
   (a------------------_in ?depot0_agent ?y ?z_0)
  )
  :effect (and
   (a_lifting ?depot0_agent ?x ?y)
   (not (a------------------_in ?depot0_agent ?y ?z_0))
   (not (a_available ?depot0_agent ?x))
))
)
