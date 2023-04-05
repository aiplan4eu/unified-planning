(define (domain pgmulti-domain)
 (:requirements :factored-privacy :typing :negative-preconditions)
 (:types location postureg stateg modeg pouchobj robot_a_type robot_b_type)
 (:constants
   active startstate - stateg
   default - postureg
   home - location
 )
 (:predicates
   (:private
   (a_at_ ?agent - robot_b_type ?loc - location)
   (a_inposg ?agent - robot_b_type ?posture - postureg)
   (a_instateg ?agent - robot_b_type ?state - stateg)))
 (:action movegripper_activate_0
  :parameters ( ?r - robot_b_type)
  :precondition (and 
   (a_instateg ?r startstate)
   (a_instateg ?r active)
  )
  :effect (and
   (a_instateg ?r active)
   (not (a_instateg ?r startstate))
   (a_inposg ?r default)
   (a_at_ ?r home)
))
)
