(define (domain simple_ma-domain)
 (:requirements :factored-privacy :typing :negative-preconditions :disjunctive-preconditions :existential-preconditions)
 (:types location door robot_a_type scale_a_type)
 (:constants
   home office - location
 )
 (:predicates
 (a_open ?agent - scale_a_type ?door - door)
  (:private
   (a_pos ?agent - robot_a_type ?loc - location)))
 (:action movegripper
  :parameters ( ?robot_a - robot_a_type)
  :precondition (and 
   (and (imply (or (not (pos ?robot_a office)) (not (pos ?robot_a home))) (pos ?robot_a home)) (imply (pos ?robot_a home) (or (not (pos ?robot_a office)) (not (pos ?robot_a home)))) )
   (and (imply (or (not (a_pos ?robot_a office)) (not (a_pos ?robot_a home))) (a_pos ?robot_a home)) (imply (a_pos ?robot_a home) (or (not (a_pos ?robot_a office)) (not (a_pos ?robot_a home)))) )
   (and (or (not (pos ?robot_a office)) (pos ?robot_a home)) (pos ?robot_a office))
   (and (or (not (a_pos ?robot_a office)) (a_pos ?robot_a home)) (a_pos ?robot_a office))
   (pos ?robot_a office)
   (a_pos ?robot_a office)
  )
  :effect (and
   (a_pos ?robot_a home)
))
)
(define (domain simple_ma-domain)
 (:requirements :factored-privacy :typing :negative-preconditions :disjunctive-preconditions :existential-preconditions)
 (:types location door robot_a_type scale_a_type)
 (:constants
   close20 open20 - door
 )
 (:predicates
 (a_pos ?agent - robot_a_type ?loc - location)
  (:private
   (a_open ?agent - scale_a_type ?door - door)))
 (:action open_door
  :parameters ( ?scale_a - scale_a_type)
  :precondition (and 
   (open ?scale_a close20)
   (a_open ?scale_a close20)
  )
  :effect (and
   (a_open ?scale_a open20)
))
)
