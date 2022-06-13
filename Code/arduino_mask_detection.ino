char serialData;
char val;
int led = 13;
int ir = 2;

void setup(){
  pinMode(led, OUTPUT);
  pinMode(ir, INPUT);
  Serial.begin(9600);
}

void loop(){
  if (Serial.available() > 0){
    serialData = Serial.read();

    if (serialData == '1') {
      digitalWrite(led, HIGH);
    }
    else if (serialData == '0'){
      digitalWrite(led, LOW);
    }
  }
  
  else{
    val = digitalRead(ir);
    Serial.print(val);
    if (val == HIGH){
      Serial.write('1');
    }
    else if (val == LOW){
      Serial.write('0');
    }
  }
}
