(define (domain pgmulti-domain)
 (:requirements :factored-privacy :typing :negative-preconditions)
 (:types location postureg stateg modeg pouchobj robot_a_type robot_b_type)
 (:predicates
   (:private
   (a_at_ ?agent - robot_b_type ?loc - location)
   (a_inposg ?agent - robot_b_type ?posture - postureg)
   (a_instateg ?agent - robot_b_type ?state - stateg)))
)
