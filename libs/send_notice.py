import smtplib #, ssl

def send_email(receiver_email,jobid,status):

  port = "25"  # For starttls
  smtp_server = "smtp.csc.fi"
  sender_email = "jarno.laitinen@csc.fi"

  receiver_email = "jarno.laitinen@csc.fi"
  #password = input("Type your password and press enter:")
  msg = "From: RD Plaform <jarno.laitinen@csc.fi>\n"
  msg = msg + "To: "+receiver_email+"\n"
  msg = msg + "Subject: RD Pipeline job information\n"
  msg = msg + "Your Job "+jobid+" has finished with status "+status+".\n"
  if status == 'COMPLETE':
    msg = msg + " You can fetch the output files.\n"
  else:
    msg = msg + "You can see job error with the script with parameter -l "+jobid

  try:
    server=  smtplib.SMTP(smtp_server, port)
    server.sendmail(sender_email, receiver_email, msg)
  except SMTPException:
    print("error sending email")
  server.quit()
  return ''

