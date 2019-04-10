LocalControllerProtoPath = /home/P4/Implementation/Local-Controller/proto
MainControllerProtoPath = /home/P4/Implementation/Controller-Implementation/proto

clean:
	rm *_pb2*
	rm $(LocalControllerProtoPath)/*_pb2*
	rm $(MainControllerProtoPath)/*_pb2*

connection:
	python -m grpc_tools.protoc -I./ --python_out=. --grpc_python_out=. connection.proto
	cp connection_pb2*  $(LocalControllerProtoPath)/
	cp connection_pb2* $(MainControllerProtoPath)/
	rm *_pb2*
