---
layout: default
title: "contact"
author: "jurnal"
permalink: /contact
---

<style>
.contact-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  font-weight: bold;
}

input[type="text"],
input[type="email"],
textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

textarea {
  resize: vertical;
}

.submit-btn {
  background-color: #007bff;
  color: #fff;
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.submit-btn:hover {
  background-color: #0056b3;
}

.contact-info {
  margin-top: 20px;
}

.contact-info ul {
  list-style: none;
  padding: 0;
}

.contact-info li {
  margin-bottom: 10px;
}

</style>

<div class="contact-container">
  <h1>Contact Us</h1>
  <p>Have a question or need assistance? Fill out the form below and we'll get back to you as soon as possible.</p>
  
  <form action="https://formspree.io/f/mgegywer" method="POST">
    <div class="form-group">
      <label for="name">Your Name:</label>
      <input type="text" id="name" name="name" required>
    </div>
    <div class="form-group">
      <label for="email">Your Email:</label>
      <input type="email" id="email" name="_replyto" required>
    </div>
    <div class="form-group">
      <label for="message">Your Message:</label>
      <textarea id="message" name="message" rows="5" required></textarea>
    </div>
    <button type="submit" class="submit-btn">Send Message</button>
  </form>

  <div class="contact-info">
    <p>Or, you can also contact us via:</p>
    <ul>
      <li>Email Address: <a href="mailto:jurnal@jurnalharianregional.com">jurnal@jurnalharianregional.com</a></li>
      <li>Phone Number: <a href="tel:+6283817490576">+6283817490576</a></li>
    </ul>
  </div>
</div>