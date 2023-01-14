; Snake by Mau Magnaguagno
(define (domain snake)
  (:requirements :hierarchy :typing :equality :negative-preconditions :method-preconditions :universal-preconditions)

  (:types snake location)

  (:predicates
    (occupied ?pos - location)
    (adjacent ?pos1 ?pos2 - location)
    (head ?snake - snake ?headpos - location)
    (connected ?snake - snake ?bodypos1 ?bodypos2 - location)
    (tail ?snake - snake ?tailpos - location)
    (mouse-at ?foodpos - location)
  )
  
  (:task hunt :parameters ())
  (:task move :parameters (?snake - snake ?snakepos ?goalpos - location))

  (:method hunt_all
    :parameters (?snake - snake ?foodpos ?snakepos ?pos1 - location)
    :task (hunt)
    :precondition (and
      (mouse-at ?foodpos)
      (head ?snake ?snakepos)
      (adjacent ?foodpos ?pos1)
    )
    :ordered-subtasks (and
      (move ?snake ?snakepos ?pos1)
      (strike ?snake ?pos1 ?foodpos)
      (hunt)
    )
  )

  (:method hunt_done
    :parameters ()
    :task (hunt)
    :precondition (forall (?pos - location) (not (mouse-at ?pos)))
    :subtasks ()
  )

  (:method move-base
    :parameters (?snake - snake ?snakepos ?goalpos - location)
    :task (move ?snake ?snakepos ?goalpos)
    :precondition (= ?snakepos ?goalpos)
    :subtasks ()
  )

  (:method move-long-snake
    :parameters (?snake - snake ?snakepos ?goalpos ?pos2 ?bodypos ?tailpos - location)
    :task (move ?snake ?snakepos ?goalpos)
    :precondition (and (adjacent ?pos2 ?snakepos) (not (occupied ?pos2)) (connected ?snake ?bodypos ?tailpos) (tail ?snake ?tailpos))
    :ordered-subtasks (and
      (move-long ?snake ?pos2 ?snakepos ?bodypos ?tailpos)
      (move ?snake ?pos2 ?goalpos)
    )
  )

  (:method move-short-snake
    :parameters (?snake - snake ?snakepos ?goalpos ?pos2 - location)
    :task (move ?snake ?snakepos ?goalpos)
    :precondition (and (adjacent ?pos2 ?snakepos) (not (occupied ?pos2)) (tail ?snake ?snakepos))
    :ordered-subtasks (and
      (move-short ?snake ?pos2 ?snakepos)
      (move ?snake ?pos2 ?goalpos)
    )
  )

  (:action strike
    :parameters (?snake - snake ?headpos ?foodpos - location)
    :precondition (and
      (head ?snake ?headpos)
      (mouse-at ?foodpos)
      (adjacent ?foodpos ?headpos)
      (not (= ?headpos ?foodpos))
    )
    :effect (and
      (not (mouse-at ?foodpos))
      (not (head ?snake ?headpos))
      (connected ?snake ?foodpos ?headpos)
      (head ?snake ?foodpos)
    )
  )

  (:action move-short
    :parameters (?snake - snake ?nextpos ?snakepos - location)
    :precondition (and
      (head ?snake ?snakepos)
      (tail ?snake ?snakepos)
      (adjacent ?nextpos ?snakepos)
      (not (occupied ?nextpos))
    )
    :effect (and
      (not (head ?snake ?snakepos))
      (not (tail ?snake ?snakepos))
      (occupied ?nextpos)
      (head ?snake ?nextpos)
      (tail ?snake ?nextpos)
      (not (occupied ?snakepos))
    )
  )

  (:action move-long
    :parameters (?snake - snake ?nextpos ?headpos ?bodypos ?tailpos - location)
    :precondition (and
      (head ?snake ?headpos)
      (connected ?snake ?bodypos ?tailpos)
      (tail ?snake ?tailpos)
      (adjacent ?nextpos ?headpos)
      (adjacent ?bodypos ?tailpos)
      (not (occupied ?nextpos))
      (not (= ?bodypos ?nextpos))
      (not (= ?tailpos ?nextpos))
      (not (= ?headpos ?tailpos))
    )
    :effect (and
      (not (head ?snake ?headpos))
      (head ?snake ?nextpos)
      (not (tail ?snake ?tailpos))
      (tail ?snake ?bodypos)
      (not (connected ?snake ?bodypos ?tailpos))
      (connected ?snake ?nextpos ?headpos)
      (occupied ?nextpos)
      (not (occupied ?tailpos))
    )
  )



)
