# Introduction to Event Driven Microservice Architectures

## Introduction

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

## Why microservices?

Microservices constitute a fundamental element within the Event Driven
Architecture. We adhere to the Unix philosophy, "do one thing and do it well".
This approach allows us to emphasize the principle of performing one task
exceptionally well. Concentrating services on specific functions enables
optimization and enhances reliability. Additionally, this approach facilitates
scaling only the services that require it, avoiding the need to scale every
service uniformly.

## You want microservices this is how you get microservices?

There are drawbacks to this approach. We can increase the complexity of the
system by increasing the number of microservices.

Microservices are most effective when they maintain a clear, well-defined scope,
but finding the right level of complexity is key. Simply increasing the number
of microservices does not necessarily enhance maintainability or scalability.

While microservices offer benefits like scalability and modularity, they also
introduce logistical challenges. Backend services typically expose versioned
APIs, requiring coordination among services. Additionally, this approach can
lead to increased network traffic, potentially causing bottlenecks if not
managed properly.

## Why Event Driven Microservice Architecture?

The microservices architecture offers a high degree of independence from the
broader system. Though it introduces additional components, effective
utilization of CI/CD and DevOps practices can empower teams to operate at
distinct development speeds and release frequencies. Embracing eventual
consistency and integrating a message-based architecture enables asynchronous
communication, fostering increased parallelism and efficient utilization of
computing resources.
