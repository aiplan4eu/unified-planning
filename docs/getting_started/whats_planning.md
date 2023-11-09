# What is automated planning?

**Automated Planning** is an area of *Artificial Intelligence* where the task is to choose and arrange actions in order to achieve some goal.

This is a pretty definition, but also a very generic one! If you are not involved in this area, this probably means nothing to you! So, we tried to come up with a way to explain automated planning, that everyone might be able to understand, and even maybe repeat to their mothers. 😉

In a simple example, think of four-year-old Tom who needs to get dressed in the morning. Every morning, he wears his pyjamas, checks what clothes are available in his drawer and his mommy tells him how warm it will be that day. In a planning task, such information would be captured by the initial state.

 
> Tom’s goal (and the one of the planning tasks) is that he is suitably dressed, considering mom’s weather forecast. 

For each piece of clothing, there is an action to put it on. The obvious effect of the action is that afterwards, Tom wears this garment. But if you ever watched a young kid getting dressed, you know that it is not that simple.

For example, one should wear a t-shirt before putting on the sweater. And one should not still wear the pyjamas when slipping into the t-shirt. In a planning task, such requirements would be formulated as preconditions of the actions. In the precondition of the corresponding action, we could also represent that winter boots are not an acceptable choice on a hot day (something Tom’s mom established by storing them away after repeated discussions).

Most (non-fashionista) adults won’t consider getting dressed a problem they need to put much thought into. But companies face analogous tasks in very different domains – with a much larger space of possible actions and much more complex interrelations.

It will take Tom several years (or at least months if you are a lucky parent!) to learn how to dress properly according to the weather and dressing preconditions. But imagine that you could teach this to your kid in a couple of days. Wouldn’t it be amazing?

The same way in companies, their employees can take weeks or even years to develop a strategy that works well, and still, its quality is oftentimes far away from optimal.

Automated planning offers a different approach to such problems: the user only describes the WHAT of the problem in a purely declarative fashion. The HOW is then resolved by the planning engine.    