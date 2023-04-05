(define (domain ma_taxi-domain)
 (:requirements :factored-privacy :typing)
 (:types location taxi ag - object
    person1_type person2_type taxi1_type taxi2_type - ag
 )
 (:predicates
  (free ?location - location)
  (directly_connected ?l1 - location ?l2 - location)
  (at_ ?taxi - taxi ?location - location)
  (empty ?taxi - taxi)
  (a_pos ?agent - ag ?location - location)
  (:private
   (a_goal_of ?agent - ag ?location - location)))
 (:action enter_p
  :parameters ( ?person1 - person1_type ?t - taxi ?l - location)
  :precondition (and 
   (a_pos ?person1 ?l)
   (at_ ?t ?l)
   (empty ?t)
  )
  :effect (and
   (not (empty ?t))
   (not (a_pos ?person1 ?l))
   (in ?t)
))
 (:action exit_p
  :parameters ( ?person1 - person1_type ?t - taxi ?l - location)
  :precondition (and 
   (in ?t)
   (at_ ?t ?l)
   (a_goal_of ?person1 ?l)
  )
  :effect (and
   (not (in ?t))
   (empty ?t)
   (a_pos ?person1 ?l)
))
)
