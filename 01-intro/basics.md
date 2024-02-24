## Introduction to Event Driven Microservice Architectures

Imagine your CI/CD pipeline as a bustling kitchen, each task like chopping
carrots or preheating the oven is an action. Now, think of Event Driven
Microservice Architecture as the central communication hub in this kitchen. It's
like a magical bulletin board capturing every action as an event. These events
aren't just scattered around; they're sent to a waiting area, which we'll call
the "Message Queue." It's like a ticket counter where events line up, waiting to
be noticed.

Now, picture specialized cooks, let's call them "watchers," keeping a keen eye
on this waiting area. They're not just any cooks; they're experts in their
craft. Only events that match their cooking expertise (or predefined criteria)
make it to their attention. They don't waste time on things that aren't their
specialty.

But here's the cool part: each watcher has a unique recipe they're passionate
about. They aren't interested in everything happening in the kitchen, just the
events that align with their culinary skills. These events reach the watchers,
and guess what they do? They swing into action, creating the magic in the
kitchen – cooking up the perfect dish!

Now, the beauty of this setup is its flexibility. It's like having different
kitchens (Message Queues) in the restaurant, each with its own specialties. The
Event Driven Architecture makes sure everything stays organized. It's like
having a system that groups watchers together based on the type of event they're
interested in – like having all the dessert experts in one corner, and the grill
masters in another.

So, in a nutshell, Event Driven Microservice Architecture is like the maestro in
the kitchen, orchestrating a symphony of actions, ensuring every event finds its
way to the right expert cook, resulting in a well-coordinated and delicious
outcome!
