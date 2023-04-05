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
   (driving ?agent - driver1_agent_type ?truck - truck)
   (pos ?agent - driver1_agent_type ?place - place)))
 (:action drive
  :parameters ( ?d - driver1_agent_type ?x_0 - truck ?y_0 - place ?z_1 - place)
  :precondition (and 
   (pos ?d ?y_0)
   (at_ ?x_0 ?y_0)
   (driving ?d ?x_0)
  )
  :effect (and
   (pos ?d ?z_1)
   (not (pos ?d ?y_0))
   (at_ ?x_0 ?z_1)
   (not (at_ ?x_0 ?y_0))
))
)
