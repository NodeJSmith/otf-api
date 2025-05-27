OTF API Client Documentation
============================

Simple API client for interacting with the OrangeTheory Fitness APIs.

.. toctree::
   :hidden:

   examples/examples_toc
   api/otf_api

Installation
------------

.. code-block:: bash

   pip install otf-api

Overview
--------

To use the API, you need to create an instance of the ``Otf`` class. This will authenticate you with the API and allow you to make requests. When the ``Otf`` object is created, it automatically grabs your member details and home studio, to simplify the process of making requests.

You can either pass an ``OtfUser`` object to the ``Otf`` class or allow it to prompt you for your username and password.

You can also export the environment variables ``OTF_EMAIL`` and ``OTF_PASSWORD`` to provide credentials implicitly.

.. code-block:: python

   from otf_api import Otf, OtfUser

   otf = Otf(user=OtfUser(<email_address>, <password>))
